import json
from pathlib import Path

import httpx
import pytest

from seoji.nlseoji.client import SeojiClient

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "nlseoji"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def make_client():
    """Build a SeojiClient whose HTTP calls are answered by `handler(request) -> Response`."""

    def make(handler, **kw):
        clock = FakeClock()
        requests: list[httpx.Request] = []

        def record(request):
            requests.append(request)
            return handler(request)

        client = SeojiClient(
            "test-key",
            http=httpx.Client(transport=httpx.MockTransport(record)),
            sleep=clock.sleep,
            clock=clock.clock,
            **kw,
        )
        return client, requests, clock

    return make


def paged_handler(request: httpx.Request) -> httpx.Response:
    page = request.url.params["page_no"]
    return httpx.Response(200, json=fixture(f"page_20220509_p{page}.json"))
