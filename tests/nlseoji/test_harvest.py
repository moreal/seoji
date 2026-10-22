from datetime import date

import httpx

from seoji.nlseoji.harvest import harvest_range, window_dates
from tests.seoji_helpers import fixture, paged_handler

DAY = date(2022, 5, 9)


def _count(db, table):
    return db.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]


def test_harvest_range_stores_bronze(db, make_client):
    client, _, _ = make_client(paged_handler)
    stats = harvest_range(db, client, DAY, DAY, page_size=2)
    assert (stats.days, stats.requests, stats.records, stats.invalid) == (1, 2, 2, 1)
    assert _count(db, "bronze.source_record") == 3
    assert _count(db, "bronze.source_record WHERE isbn13 IS NULL") == 1
    params = [
        r["request_params"] for r in db.execute("SELECT request_params FROM bronze.api_payload")
    ]
    assert params and all("cert_key" not in p for p in params)
    assert params[0]["start_publish_date"] == "20220509"


def test_harvest_twice_is_noop(db, make_client):
    client, _, _ = make_client(paged_handler)
    harvest_range(db, client, DAY, DAY, page_size=2)
    payloads = _count(db, "bronze.api_payload")
    stats = harvest_range(db, client, DAY, DAY, page_size=2)
    assert stats.changed == 0
    assert _count(db, "bronze.api_payload") == payloads


def test_harvest_shrinks_page_size_on_013(db, make_client):
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json=fixture("error_013.json"))
        return httpx.Response(200, json=fixture("page_20220509_p1.json") | {"TOTAL_COUNT": "2"})

    client, requests, _ = make_client(handler)
    harvest_range(db, client, DAY, DAY, page_size=100)
    assert requests[1].url.params["page_size"] == "50"


def test_window_dates():
    assert window_dates("daily", date(2026, 10, 22)) == (date(2026, 9, 22), date(2027, 1, 20))
    assert window_dates("weekly", date(2026, 10, 22)) == (date(2025, 10, 22), date(2026, 9, 21))
