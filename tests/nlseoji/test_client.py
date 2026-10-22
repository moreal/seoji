import httpx
import pytest

from seoji.nlseoji.client import FatalSeojiError, PageSizeTooLarge, SeojiError
from tests.seoji_helpers import fixture, paged_handler


def test_search_strips_cert_key_from_params(make_client):
    client, requests, _ = make_client(paged_handler)
    page = client.search(page_no=1, page_size=2)
    assert requests[0].url.params["cert_key"] == "test-key"
    assert requests[0].url.params["result_style"] == "json"
    assert "cert_key" not in page.params
    assert (page.total_count, page.page_no, len(page.docs)) == (3, 1, 2)


def test_error_011_raises_fatal(make_client):
    client, _, _ = make_client(lambda r: httpx.Response(200, json=fixture("error_011.json")))
    with pytest.raises(FatalSeojiError) as e:
        client.search(page_no=1, page_size=10)
    assert e.value.code == "011"


def test_error_013_raises_page_size(make_client):
    client, _, _ = make_client(lambda r: httpx.Response(200, json=fixture("error_013.json")))
    with pytest.raises(PageSizeTooLarge):
        client.search(page_no=1, page_size=1000)


def test_rate_limit_sleeps_between_calls(make_client):
    client, _, clock = make_client(paged_handler)
    client.search(page_no=1, page_size=2)
    assert clock.sleeps == []
    client.search(page_no=2, page_size=2)
    assert clock.sleeps == [1.0]


def test_retries_5xx_then_succeeds(make_client):
    calls = []

    def flaky(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503)
        return paged_handler(request)

    client, _, clock = make_client(flaky)
    assert client.search(page_no=1, page_size=2).total_count == 3
    assert len(calls) == 2 and 1.0 in clock.sleeps


def test_gives_up_after_three_retries(make_client):
    client, requests, _ = make_client(lambda r: httpx.Response(500))
    with pytest.raises(SeojiError) as e:
        client.search(page_no=1, page_size=2)
    assert len(requests) == 4
    assert "test-key" not in str(e.value)
    assert e.value.__cause__ is None and e.value.__suppress_context__


def test_client_error_does_not_leak_key(make_client):
    client, requests, _ = make_client(lambda r: httpx.Response(404))
    with pytest.raises(SeojiError) as e:
        client.search(page_no=1, page_size=2)
    assert len(requests) == 1
    assert "test-key" not in str(e.value) and "404" in str(e.value)
    assert e.value.__cause__ is None and e.value.__suppress_context__


def test_429_is_retried(make_client):
    calls = []

    def throttled(request):
        calls.append(request)
        return httpx.Response(429) if len(calls) == 1 else paged_handler(request)

    client, _, _ = make_client(throttled)
    assert client.search(page_no=1, page_size=2).total_count == 3


def test_non_json_body_is_retried_then_reported(make_client):
    client, requests, _ = make_client(lambda r: httpx.Response(200, text="<html>점검중</html>"))
    with pytest.raises(SeojiError) as e:
        client.search(page_no=1, page_size=2)
    assert len(requests) == 4
    assert "test-key" not in str(e.value)
