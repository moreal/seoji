from seoji.gold.build import rebuild_search_doc
from seoji.silver.build import refresh_silver
from tests.lod_helpers import NLK


def search(db, q, lim=20, korean_only=False):
    return db.execute(
        "SELECT * FROM gold.search_books(%s, %s, %s)", (q, lim, korean_only)
    ).fetchall()


def test_search_doc_built_with_silver(built):
    n = built.execute("SELECT count(*) AS n FROM gold.search_doc").fetchone()["n"]
    assert n == built.execute("SELECT count(*) AS n FROM silver.edition").fetchone()["n"]


def test_search_exact_title(built):
    rows = search(built, "아몬드")
    assert rows[0]["isbn13"] == "9788936434267"
    assert rows[0]["authors"] == "손원평"


def test_search_two_syllables(built):
    isbns = {r["isbn13"] for r in search(built, "재판", lim=50)}
    assert "9788993171440" in isbns


def test_search_substring_with_particle(built):
    built.execute(
        "INSERT INTO gold.search_doc (isbn13, title, search_text, is_korean)"
        " VALUES ('9791180000027', '아몬드를 먹은 소년', '아몬드를 먹은 소년', true)"
    )
    assert "9791180000027" in {r["isbn13"] for r in search(built, "아몬드")}


def test_search_author_and_title_terms(built):
    assert len(search(built, "손원평 아몬드")) >= 1
    assert search(built, "손원평 헌터") == []


def test_search_is_case_and_width_insensitive(built):
    assert {r["isbn13"] for r in search(built, "ＫＯＴＲＡ")} == {"9791160979053"}


def test_search_escapes_wildcards(built):
    assert search(built, "%") == []
    assert search(built, "   ") == []


def test_korean_only_filter(built):
    assert search(built, "臺灣") != []
    assert search(built, "臺灣", korean_only=True) == []


def test_refresh_updates_search_doc(built, make_nt):
    from seoji.lod.load import load_dump

    load_dump(
        built,
        make_nt("retitled.nt", retitle={NLK + "KJU201703899": "호두"}),
        dataset="book",
        fmt="nt",
        dump_date=None,
    )
    refresh_silver(built)
    assert all(r["isbn13"] != "9788936434267" for r in search(built, "아몬드"))
    assert search(built, "호두")[0]["isbn13"] == "9788936434267"


def test_partial_rebuild(built):
    built.execute("DELETE FROM gold.search_doc")
    assert rebuild_search_doc(built, ["9788936434267"]) == 1
    assert [r["isbn13"] for r in search(built, "아몬드")] == ["9788936434267"]


def test_search_by_title_and_volume(built):
    assert "9788925807164" in {r["isbn13"] for r in search(built, "오토멘 제4권")}


def test_search_offset_pages_through_results(built):
    first = built.execute("SELECT isbn13 FROM gold.search_books('재판', 3, false, 0)").fetchall()
    second = built.execute("SELECT isbn13 FROM gold.search_books('재판', 3, false, 3)").fetchall()
    assert first and second
    assert not {r["isbn13"] for r in first} & {r["isbn13"] for r in second}


def test_takedown_hides_from_search(built):
    built.execute("INSERT INTO gold.takedown (isbn13, reason) VALUES ('9788936434267', 'test')")
    assert all(r["isbn13"] != "9788936434267" for r in search(built, "아몬드"))


def test_search_ranks_a_capped_candidate_set(built):
    rows = built.execute("SELECT isbn13 FROM gold.search_books('재판', 10, false, 0, 1)").fetchall()
    assert len(rows) == 1
