import contextlib
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout
from starlette.middleware.trustedhost import TrustedHostMiddleware

from seoji import query
from seoji.config import Settings
from seoji.query import QueryError
from seoji.server.mcp import build_mcp
from seoji.server.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
API_CACHE = "public, max-age=300"
STATEMENT_TIMEOUT = "3s"
POOL_TIMEOUT = 2.0  # seconds to wait for a free connection before answering 503


PUBLIC_ROLE = "seoji_public"


def _configure_for(settings: Settings):
    def configure(conn: psycopg.Connection) -> None:
        # Without a dedicated login, drop to the SELECT-only role for every pooled connection.
        # (A login as seoji_public is stronger: a session cannot RESET ROLE back to its owner.)
        if not settings.public_database_url:
            conn.execute(f"SET ROLE {PUBLIC_ROLE}")
        conn.execute("SET default_transaction_read_only = on")
        conn.execute(f"SET statement_timeout = '{STATEMENT_TIMEOUT}'")

    return configure


def make_pool(settings: Settings) -> ConnectionPool:
    return ConnectionPool(
        settings.public_database_url or settings.database_url,
        min_size=1,
        max_size=10,
        kwargs={"row_factory": dict_row, "autocommit": True},
        configure=_configure_for(settings),
        open=False,
    )


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def create_app(settings: Settings) -> FastAPI:
    pool = make_pool(settings)
    mcp = build_mcp(settings, pool, pool_timeout=POOL_TIMEOUT)
    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=True, json_response=True,
        transport_security=mcp_transport_security(settings),
    )  # fmt: skip

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        pool.open(wait=True)
        try:
            async with mcp.session_manager.run():
                yield
        finally:
            pool.close()

    app = FastAPI(
        title="seoji",
        description=f"{query.ATTRIBUTION}. {query.NOTICE}",
        lifespan=lifespan,
        docs_url=None,  # Swagger UI loads scripts from a CDN, which the CSP rightly blocks
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.pool = pool
    app.state.settings = settings

    def conn():
        with pool.connection(timeout=POOL_TIMEOUT) as c:
            yield c

    Conn = Annotated[psycopg.Connection, Depends(conn)]

    @app.exception_handler(QueryError)
    async def query_error(request: Request, exc: QueryError):
        return _error(400, exc.code, exc.message)

    @app.exception_handler(psycopg.errors.QueryCanceled)
    async def query_timeout(request: Request, exc: psycopg.errors.QueryCanceled):
        return _error(
            503, "query_timeout", "검색이 너무 오래 걸립니다. 검색어를 더 구체적으로 입력하세요"
        )

    @app.exception_handler(PoolTimeout)
    async def busy(request: Request, exc: PoolTimeout):
        return _error(503, "busy", "서버가 바쁩니다. 잠시 후 다시 시도하세요")

    @app.exception_handler(psycopg.Error)
    async def db_error(request: Request, exc: psycopg.Error):
        return _error(503, "db_error", "데이터베이스 오류가 발생했습니다")

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return _error(400, "invalid_request", "요청 파라미터가 올바르지 않습니다")

    @app.get("/api/v1/search")
    def search(
        response: Response,
        c: Conn,
        q: Annotated[str, Query(description="검색어 (제목·저자·출판사·총서·권차)")],
        limit: int = 20,
        offset: int = 0,
        korean_only: bool = False,
    ):
        response.headers["cache-control"] = API_CACHE
        return query.search(c, q, limit=limit, offset=offset, korean_only=korean_only)

    @app.get("/api/v1/books/{isbn}")
    def book(isbn: str, response: Response, c: Conn):
        found = query.get_book(c, isbn, include_rich_text=settings.public_rich_text)
        if found is None:
            return _error(404, "not_found", "해당 ISBN의 책이 없습니다")
        response.headers["cache-control"] = API_CACHE
        return found

    @app.get("/api/v1/sets/{isbn}")
    def book_set(isbn: str, response: Response, c: Conn):
        found = query.get_set(c, isbn)
        if found is None:
            return _error(404, "not_found", "해당 ISBN의 세트가 없습니다")
        response.headers["cache-control"] = API_CACHE
        return found

    @app.get("/api/v1/meta")
    def meta(c: Conn):
        return query.meta(c, settings)

    @app.get("/healthz")
    def healthz(c: Conn):
        c.execute("SELECT 1")
        return {"ok": True}

    # The MCP sub-app is a single Route at /mcp with no middleware of its own; adding the route
    # directly (rather than mounting) serves /mcp itself instead of only /mcp/.
    app.router.routes.extend(mcp_app.routes)
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

    # The last one added runs outermost. Order, outside in: security headers (so even 400 and
    # 429 responses carry them), CORS, host check, then the rate limit.
    app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET"]
        )
    app.add_middleware(SecurityHeadersMiddleware)
    return app


def mcp_transport_security(settings: Settings):
    from mcp.server.transport_security import TransportSecuritySettings

    hosts = list(settings.allowed_hosts)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts + [f"{h}:*" for h in hosts],
        allowed_origins=[f"{scheme}://{h}{port}" for h in hosts for scheme in ("http", "https")
                         for port in ("", ":*")],
    )  # fmt: skip
