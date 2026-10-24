from datetime import date

from seoji.lod.load import load_dump
from seoji.silver.build import rebuild_silver, refresh_silver
from tests.lod_helpers import NLK

ALMOND = "9788936434267"
TRIAL_SET = "9788993171440"


def one(db, sql, *params):
    return db.execute(sql, params).fetchone()


def test_rebuild_creates_editions_and_sets(loaded):
    stats = rebuild_silver(loaded)
    assert stats.editions > 0
    members = loaded.execute(
        "SELECT isbn13 FROM silver.set_member WHERE set_isbn13 = %s", (TRIAL_SET,)
    ).fetchall()
    assert len(members) == 6
    assert one(loaded, "SELECT 1 AS ok FROM silver.book_set WHERE set_isbn13 = %s", TRIAL_SET)
    linked = one(
        loaded,
        "SELECT count(*) AS n FROM silver.edition_record_link WHERE source_key = %s",
        NLK + "KJU201211257",
    )["n"]
    assert linked == 7


def test_almond_edition_merges_lod_and_seoji(loaded):
    rebuild_silver(loaded)
    e = one(loaded, "SELECT * FROM silver.edition WHERE isbn13 = %s", ALMOND)
    assert e["title"] == "아몬드"
    assert e["is_korean"] is True
    assert e["isbn10"] == "8936434268"
    assert e["price_planned"] == 16800
    assert e["pub_status"] == "published"
    assert e["add_reader"] == "4"
    assert e["provenance"]["title"] == "lod" and e["provenance"]["price_planned"] == "nlseoji"
    assert (
        one(
            loaded, "SELECT count(*) AS n FROM silver.edition_contributor WHERE isbn13 = %s", ALMOND
        )["n"]
        == 1
    )
    assert (
        one(
            loaded,
            "SELECT count(*) AS n FROM silver.edition_subject WHERE isbn13 = %s AND scheme = 'ksh'",
            ALMOND,
        )["n"]
        == 2
    )
    rich = one(loaded, "SELECT * FROM silver.edition_rich_text WHERE isbn13 = %s", ALMOND)
    assert rich["kind"] == "introduction" and rich["redistributable"] is False
    sources = {
        r["source"]
        for r in loaded.execute(
            "SELECT source FROM silver.edition_record_link WHERE isbn13 = %s", (ALMOND,)
        )
    }
    assert sources == {"lod", "nlseoji"}


def test_foreign_isbn_not_korean(loaded):
    rebuild_silver(loaded)
    assert one(loaded, "SELECT count(*) AS n FROM silver.edition WHERE NOT is_korean")["n"] >= 1


def test_no_isbn_resource(loaded):
    rebuild_silver(loaded)
    row = one(
        loaded,
        "SELECT * FROM silver.manifestation_no_isbn WHERE resource_uri = %s",
        NLK + "CMO000000001",
    )
    assert row["issued_year"] == 1984


def test_invalid_isbn_issues(loaded):
    rebuild_silver(loaded)
    keys = {
        (r["source"], r["source_key"])
        for r in loaded.execute("SELECT * FROM silver.merge_issue WHERE kind = 'invalid_isbn'")
    }
    assert ("nlseoji", "9788936434268") in keys
    assert ("lod", NLK + "CMO000000042") in keys


def test_seoji_only_edition_is_announced(loaded):
    rebuild_silver(loaded)
    e = one(loaded, "SELECT * FROM silver.edition WHERE isbn13 = '9791180000010'")
    assert (e["pub_status"], e["binding"]) == ("announced", "ebook")
    assert (
        one(loaded, "SELECT total_volumes FROM silver.book_set WHERE set_isbn13 = '9791180000003'")[
            "total_volumes"
        ]
        == 2
    )


def test_rebuild_is_deterministic(loaded):
    rebuild_silver(loaded)
    first = {
        r["isbn13"]: bytes(r["content_hash"])
        for r in loaded.execute("SELECT isbn13, content_hash FROM silver.edition")
    }
    rebuild_silver(loaded)
    second = {
        r["isbn13"]: bytes(r["content_hash"])
        for r in loaded.execute("SELECT isbn13, content_hash FROM silver.edition")
    }
    assert first == second


def test_refresh_only_touches_changed(loaded, make_nt):
    rebuild_silver(loaded)
    load_dump(
        loaded,
        make_nt("retitled.nt", retitle={NLK + "KJU201703899": "아몬드 개정판"}),
        dataset="book",
        fmt="nt",
        dump_date=None,
    )
    stats = refresh_silver(loaded)
    assert stats.editions == 1
    assert one(loaded, "SELECT title FROM silver.edition WHERE isbn13 = %s", ALMOND)["title"] == (
        "아몬드 개정판"
    )


def test_refresh_with_nothing_changed(loaded):
    rebuild_silver(loaded)
    assert refresh_silver(loaded).editions == 0


def test_refresh_removes_tombstoned(db, make_nt):
    from tests.lod_helpers import SAMPLE_KR

    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    rebuild_silver(db)
    load_dump(
        db,
        make_nt("no_almond.nt", drop={NLK + "KJU201703899"}),
        dataset="book",
        fmt="nt",
        dump_date=None,
        mark_missing=True,
    )
    refresh_silver(db)
    assert one(db, "SELECT 1 AS ok FROM silver.edition WHERE isbn13 = %s", ALMOND) is None


def _sets(db):
    sets = db.execute("SELECT * FROM silver.book_set ORDER BY set_isbn13").fetchall()
    members = db.execute("SELECT * FROM silver.set_member ORDER BY set_isbn13, isbn13").fetchall()
    return sets, members


def test_refresh_drops_sets_of_tombstoned_resources(loaded, make_nt):
    rebuild_silver(loaded)
    load_dump(
        loaded,
        make_nt("no_set.nt", drop={NLK + "KJU201108521"}),
        dataset="book",
        fmt="nt",
        dump_date=None,
        mark_missing=True,
    )
    refresh_silver(loaded)
    assert (
        one(loaded, "SELECT 1 AS ok FROM silver.book_set WHERE set_isbn13 = '9791189431907'")
        is None
    )


def test_refresh_sets_match_rebuild(loaded, make_nt):
    rebuild_silver(loaded)
    load_dump(
        loaded,
        make_nt("fewer.nt", drop={NLK + "KJU201108521", NLK + "KJU201211257"}),
        dataset="book",
        fmt="nt",
        dump_date=None,
        mark_missing=True,
    )
    refresh_silver(loaded)
    after_refresh = _sets(loaded)
    rebuild_silver(loaded)
    assert after_refresh == _sets(loaded)


def test_seoji_set_expression_change_is_not_sticky(loaded):
    rebuild_silver(loaded)
    loaded.execute(
        'UPDATE bronze.source_record SET record = record || \'{"SET_EXPRESSION": "세트"}\','
        " changed_at = clock_timestamp() WHERE source_key = '9791180000010'"
    )
    loaded.commit()
    refresh_silver(loaded)
    row = one(loaded, "SELECT * FROM silver.book_set WHERE set_isbn13 = '9791180000003'")
    assert (row["set_expression"], row["total_volumes"], row["is_open_ended"]) == (
        "세트",
        None,
        True,
    )


def test_real_seoji_set_record_fills_book_set(db, make_client):
    import httpx

    from seoji.nlseoji.harvest import harvest_range
    from tests.seoji_helpers import fixture

    docs = fixture("real_20220509_sample.json")["docs"]
    page = {"PAGE_NO": "1", "TOTAL_COUNT": str(len(docs)), "docs": docs}
    client, _, _ = make_client(lambda r: httpx.Response(200, json=page))
    harvest_range(db, client, date(2022, 5, 9), date(2022, 5, 9), page_size=100)
    rebuild_silver(db)
    s = one(db, "SELECT * FROM silver.book_set WHERE set_isbn13 = '9791169031547'")
    assert (s["set_expression"], s["total_volumes"], s["is_open_ended"]) == ("전6권", 6, False)
    assert s["title"] == "죄악은 흔적을 남긴다(세트)"
    members = db.execute(
        "SELECT count(*) AS n FROM silver.set_member WHERE set_isbn13 = '9791169031547'"
    ).fetchone()["n"]
    assert members == 2


def test_malformed_set_add_code_does_not_break_rebuild(db, make_client):
    import httpx

    from seoji.nlseoji.harvest import harvest_range
    from tests.seoji_helpers import fixture

    doc = {k: v for k, v in fixture("real_20220509_sample.json")["docs"][2].items() if k != "_case"}
    doc |= {"SET_ADD_CODE": "0581012"}
    page = {"PAGE_NO": "1", "TOTAL_COUNT": "1", "docs": [doc]}
    client, _, _ = make_client(lambda r: httpx.Response(200, json=page))
    harvest_range(db, client, date(2022, 5, 9), date(2022, 5, 9), page_size=10)
    rebuild_silver(db)
    row = one(db, "SELECT set_add_code FROM silver.book_set WHERE set_isbn13 = %s", doc["SET_ISBN"])
    assert row["set_add_code"] is None
