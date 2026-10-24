"""Pure ASGI middleware (no BaseHTTPMiddleware, so streamed MCP responses pass through)."""

import ipaddress
import json
import math
import time
from collections import OrderedDict, deque
from collections.abc import Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from seoji.query import COVER_HOSTS

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    f"img-src 'self' {' '.join(f'https://{h}' for h in COVER_HOSTS)}; "
    "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
SECURITY_HEADERS = [
    (b"content-security-policy", CSP.encode()),
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-frame-options", b"DENY"),
    (b"cross-origin-opener-policy", b"same-origin"),
]


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                names = {k for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    (k, v) for k, v in SECURITY_HEADERS if k not in names
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)


def client_key(addr: str) -> str:
    """Rate-limit bucket for an address: IPv4 as is, IPv6 by /64 (one subscriber's prefix)."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return addr
    if ip.version == 6:
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)


class RateLimitMiddleware:
    """Sliding one-minute window and a concurrency cap per client, for the given path prefixes.

    The client address is what the ASGI server reports; behind a reverse proxy, run uvicorn
    with proxy headers enabled (seoji serve does this when SEOJI_TRUST_FORWARDED_FOR is set).
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        per_minute: int,
        max_concurrent: int = 4,
        prefixes: tuple[str, ...] = ("/api/", "/mcp", "/healthz"),
        max_clients: int = 100_000,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.app = app
        self.per_minute = per_minute
        self.max_concurrent = max_concurrent
        self.in_flight: dict[str, int] = {}
        self.prefixes = prefixes
        self.max_clients = max_clients
        self.clock = clock
        self.hits: OrderedDict[str, deque[float]] = OrderedDict()

    def _allow(self, key: str) -> float | None:
        """Record a hit; return seconds to wait when over the limit, else None."""
        now = self.clock()
        window = self.hits.pop(key, None) or deque()
        while window and now - window[0] >= 60:
            window.popleft()
        self.hits[key] = window  # most recently seen last
        while len(self.hits) > self.max_clients:
            self.hits.popitem(last=False)
        if len(window) >= self.per_minute:
            return max(1.0, 60 - (now - window[0]))
        window.append(now)
        return None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(self.prefixes):
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        key = client_key(client[0]) if client else "unknown"
        if self.in_flight.get(key, 0) >= self.max_concurrent:
            await self._reject(send, 1.0, "동시 요청이 너무 많습니다")
            return
        wait = self._allow(key)
        if wait is not None:
            await self._reject(send, wait, "요청이 너무 많습니다")
            return
        self.in_flight[key] = self.in_flight.get(key, 0) + 1
        try:
            await self.app(scope, receive, send)
        finally:
            self.in_flight[key] -= 1
            if not self.in_flight[key]:
                del self.in_flight[key]

    async def _reject(self, send: Send, wait: float, message: str) -> None:
        body = json.dumps(
            {"error": {"code": "rate_limited", "message": message}}, ensure_ascii=False
        ).encode()
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
                (b"retry-after", str(math.ceil(wait)).encode()),
                (b"content-length", str(len(body)).encode()),
            ],
        })  # fmt: skip
        await send({"type": "http.response.body", "body": body})
