"""MCP tools over the same public query layer as the REST API."""

from typing import Any

import anyio
import psycopg
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from psycopg_pool import ConnectionPool, PoolTimeout

from seoji import query as queries
from seoji.config import Settings
from seoji.query import QueryError

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)


def build_mcp(settings: Settings, pool: ConnectionPool, *, pool_timeout: float = 2.0) -> MCPServer:
    mcp = MCPServer(
        name="seoji",
        instructions=(
            "한국 도서 서지 데이터(국립중앙도서관 Seoji·국가서지 LOD) 검색 도구입니다. "
            f"{queries.NOTICE} 결과를 인용할 때는 출처를 함께 밝혀 주세요: {queries.ATTRIBUTION}"
        ),
    )

    async def run(fn, *args, **kwargs):
        def call():
            with pool.connection(timeout=pool_timeout) as conn:
                return fn(conn, *args, **kwargs)

        try:
            return await anyio.to_thread.run_sync(call)
        except QueryError as e:
            raise ToolError(f"{e.code}: {e.message}") from None
        except psycopg.errors.QueryCanceled:
            raise ToolError("query_timeout: 검색어를 더 구체적으로 입력하세요") from None
        except PoolTimeout:
            raise ToolError("busy: 서버가 바쁩니다. 잠시 후 다시 시도하세요") from None
        except psycopg.Error:
            raise ToolError("db_error: 데이터베이스 오류가 발생했습니다") from None

    @mcp.tool(annotations=READ_ONLY, structured_output=True)
    async def search_books(
        query: str, limit: int = 10, offset: int = 0, korean_only: bool = False
    ) -> dict[str, Any]:
        """제목·저자·출판사·총서명·권차로 책을 검색합니다. 공백으로 나눈 모든 단어가 들어간 책만
        찾습니다(부분 일치). limit은 1~50, offset은 0~1000입니다."""
        return await run(queries.search, query, limit=limit, offset=offset,
                         korean_only=korean_only)  # fmt: skip

    @mcp.tool(annotations=READ_ONLY, structured_output=True)
    async def get_book(isbn: str) -> dict[str, Any]:
        """ISBN(10자리·13자리, 하이픈 허용)으로 책 한 권의 서지 정보를 가져옵니다."""
        book = await run(queries.get_book, isbn, include_rich_text=settings.public_rich_text)
        if book is None:
            raise ToolError("not_found: 해당 ISBN의 책이 없습니다")
        return book

    @mcp.tool(annotations=READ_ONLY, structured_output=True)
    async def get_book_set(set_isbn: str) -> dict[str, Any]:
        """세트 ISBN으로 세트 정보와 소속 권 목록을 가져옵니다."""
        found = await run(queries.get_set, set_isbn)
        if found is None:
            raise ToolError("not_found: 해당 ISBN의 세트가 없습니다")
        return found

    return mcp
