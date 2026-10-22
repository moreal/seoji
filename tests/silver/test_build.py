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
