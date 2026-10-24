import json

import pytest
from mcp.client.client import Client

from seoji.config import Settings
from seoji.server.app import make_pool
from seoji.server.mcp import build_mcp

ALMOND = "9788936434267"
MCP_HEADERS = {"accept": "application/json, text/event-stream", "content-type": "application/json"}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mcp_server(built, migrated_url):
    pool = make_pool(Settings(database_url=migrated_url, seoji_cert_key=None))
    pool.open(wait=True)
    yield build_mcp(Settings(database_url=migrated_url, seoji_cert_key=None), pool)
    pool.close()


@pytest.mark.anyio
async def test_tools_are_read_only(mcp_server):
    async with Client(mcp_server) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == {"search_books", "get_book", "get_book_set"}
    assert all(t.annotations.read_only_hint for t in tools.values())


@pytest.mark.anyio
async def test_search_and_get_book(mcp_server):
    async with Client(mcp_server) as client:
        found = await client.call_tool("search_books", {"query": "아몬드"})
        book = await client.call_tool("get_book", {"isbn": "978-89-364-3426-7"})
    assert found.structured_content["items"][0]["isbn13"] == ALMOND
    assert book.structured_content["title"] == "아몬드"
    assert "rich_text" not in book.structured_content


@pytest.mark.anyio
async def test_tool_errors_are_reported(mcp_server):
    async with Client(mcp_server) as client:
        too_many = await client.call_tool("search_books", {"query": "아몬드", "limit": 500})
        missing = await client.call_tool("get_book", {"isbn": "9791180000027"})
    assert too_many.is_error and "limit_out_of_range" in too_many.content[0].text
    assert missing.is_error and "not_found" in missing.content[0].text


def _initialize(api, **headers):
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"}}}  # fmt: skip
    return api.post("/mcp", content=json.dumps(body), headers=MCP_HEADERS | headers)


def test_mcp_over_http(api):
    r = _initialize(api)
    assert r.status_code == 200, r.text
    assert r.json()["result"]["serverInfo"]["name"] == "seoji"


def test_mcp_rejects_foreign_origin(api):
    assert _initialize(api, origin="https://evil.example.com").status_code in (400, 403)


def test_mcp_is_rate_limited(make_api):
    client = make_api(rate_limit_per_minute=2)
    assert [_initialize(client).status_code for _ in range(3)][-1] == 429
