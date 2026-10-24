import pytest
from fastapi.testclient import TestClient

from seoji.config import Settings
from seoji.server.app import create_app


@pytest.fixture
def make_api(built, migrated_url):
    """TestClient factory over the fixture-built database; pass Settings overrides."""
    clients = []

    def make(**overrides) -> TestClient:
        settings = Settings(
            database_url=migrated_url, seoji_cert_key=None, contact="takedown@example.org",
            rate_limit_per_minute=1000, allowed_hosts=("localhost",),
        ) if not overrides else Settings(
            **{"database_url": migrated_url, "seoji_cert_key": None,
               "contact": "takedown@example.org", "rate_limit_per_minute": 1000,
               "allowed_hosts": ("localhost",), **overrides}
        )  # fmt: skip
        client = TestClient(create_app(settings), base_url="http://localhost")
        client.__enter__()
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def api(make_api):
    return make_api()
