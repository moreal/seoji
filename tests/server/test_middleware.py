import anyio
import pytest

from seoji.server.middleware import RateLimitMiddleware, client_key


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.parametrize(
    "addr, key",
    [
        ("203.0.113.7", "203.0.113.7"),
        ("2001:db8:1:2:3:4:5:6", "2001:db8:1:2::/64"),
        ("2001:db8:1:2:ffff::1", "2001:db8:1:2::/64"),
        ("not-an-ip", "not-an-ip"),
    ],
)
def test_client_key_groups_ipv6_by_64(addr, key):
    assert client_key(addr) == key


@pytest.mark.anyio
async def test_concurrent_requests_per_client_are_capped():
    release = anyio.Event()
    started = 0

    async def slow_app(scope, receive, send):
        nonlocal started
        started += 1
        await release.wait()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = RateLimitMiddleware(slow_app, per_minute=100, max_concurrent=2)
    statuses = []

    async def request():
        scope = {"type": "http", "path": "/api/v1/search", "client": ("203.0.113.7", 1)}

        async def send(message):
            if message["type"] == "http.response.start":
                statuses.append(message["status"])

        await middleware(scope, None, send)

    async with anyio.create_task_group() as tg:
        for _ in range(3):
            tg.start_soon(request)
        await anyio.sleep(0.05)
        assert statuses == [429]
        release.set()
    assert sorted(statuses) == [200, 200, 429] and started == 2
    await request()  # slots are released afterwards
    assert statuses[-1] == 200
