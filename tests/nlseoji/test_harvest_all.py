import httpx
import pytest

from seoji.nlseoji.harvest import harvest_all
from tests.seoji_helpers import fixture

DOCS = [
    {k: v for k, v in d.items() if k != "_case"}
    for d in fixture("real_20220509_sample.json")["docs"]
]


def paging(request: httpx.Request) -> httpx.Response:
    page, size = int(request.url.params["page_no"]), int(request.url.params["page_size"])
    chunk = DOCS[(page - 1) * size : page * size]
    return httpx.Response(
        200, json={"PAGE_NO": str(page), "TOTAL_COUNT": str(len(DOCS)), "docs": chunk}
    )


def pages(requests) -> list[int]:
    return [int(r.url.params["page_no"]) for r in requests]


def cursor(db):
    return db.execute("SELECT * FROM bronze.harvest_cursor WHERE name = 'nlseoji_all'").fetchone()


def test_pages_through_everything_without_filters(db, make_client):
    client, requests, _ = make_client(paging)
    stats = harvest_all(db, client, page_size=3)
    assert pages(requests) == [1, 2, 3]
    params = requests[0].url.params
    assert (params["sort"], params["order_by"], params["page_size"]) == ("INPUT_DATE", "ASC", "3")
    assert "start_publish_date" not in params and "end_publish_date" not in params
    assert (stats.records, stats.total_count) == (len(DOCS), len(DOCS))
    n = db.execute("SELECT count(*) AS n FROM bronze.source_record").fetchone()["n"]
    assert n == len(DOCS)
    c = cursor(db)
    assert (c["page_no"], c["page_size"], c["total_count"]) == (3, 3, len(DOCS))
    assert c["completed_at"] is not None


def test_resumes_from_last_committed_page(db, make_client):
    client, requests, _ = make_client(paging)
    harvest_all(db, client, page_size=3, max_pages=1)
    assert cursor(db)["page_no"] == 1 and cursor(db)["completed_at"] is None
    requests.clear()
    harvest_all(db, client, page_size=3)
    assert pages(requests) == [1, 2, 3]


def test_completed_run_only_rechecks_the_tail(db, make_client):
    client, requests, _ = make_client(paging)
    harvest_all(db, client, page_size=3)
    requests.clear()
    stats = harvest_all(db, client, page_size=3)
    assert pages(requests) == [3]
    assert stats.changed == 0


def test_restart_begins_at_first_page(db, make_client):
    client, requests, _ = make_client(paging)
    harvest_all(db, client, page_size=3)
    requests.clear()
    harvest_all(db, client, page_size=3, restart=True)
    assert pages(requests) == [1, 2, 3]


def test_page_size_change_keeps_record_offset(db, make_client):
    client, requests, _ = make_client(paging)
    harvest_all(db, client, page_size=3, max_pages=2)  # records 0..5 committed
    requests.clear()
    harvest_all(db, client, page_size=2)
    # last committed page (records 3..5) starts at offset 3 -> page 2 of size 2
    assert pages(requests) == [2, 3, 4]


@pytest.mark.parametrize("first_size,expected", [(1000, "500")])
def test_shrinks_page_size_on_013(db, make_client, first_size, expected):
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json=fixture("error_013.json"))
        return paging(request)

    client, requests, _ = make_client(handler)
    harvest_all(db, client, page_size=first_size)
    assert requests[1].url.params["page_size"] == expected
    assert cursor(db)["page_size"] == int(expected)


def test_reports_progress_per_page(db, make_client):
    client, _, _ = make_client(paging)
    seen = []
    harvest_all(
        db, client, page_size=3, on_page=lambda page, size, total: seen.append((page, size, total))
    )
    assert seen == [(1, 3, 8), (2, 3, 8), (3, 3, 8)]
