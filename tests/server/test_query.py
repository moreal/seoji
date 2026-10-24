import pytest

from seoji import query
from seoji.query import QueryError

ALMOND = "9788936434267"
TRIAL_SET = "9788993171440"
RICH_KEYS = {"rich_text", "introduction", "toc", "summary", "abstract"}


def test_search_items_expose_only_listed_fields(built):
    result = query.search(built, "아몬드")
    assert result["items"][0]["isbn13"] == ALMOND
    assert set(result["items"][0]) == set(query.SEARCH_ITEM_FIELDS)
    assert result["has_more"] is False


def test_search_has_more(built):
    result = query.search(built, "재판", limit=2)
    assert len(result["items"]) == 2 and result["has_more"] is True


@pytest.mark.parametrize(
    "kwargs, code",
    [
        ({"q": "아몬드", "limit": 51}, "limit_out_of_range"),
        ({"q": "아몬드", "limit": 0}, "limit_out_of_range"),
        ({"q": "아몬드", "offset": 1001}, "offset_out_of_range"),
        ({"q": "아몬드", "offset": -1}, "offset_out_of_range"),
        ({"q": "   "}, "empty_query"),
        ({"q": "가" * 101}, "query_too_long"),
        ({"q": "\ufdfa" * 10}, "query_too_long"),  # 10 chars, 180 after NFKC
        ({"q": " ".join("이" * 9)}, "too_many_terms"),
        ({"q": "abc\x00def"}, "invalid_query"),
        ({"q": "abc\x07def"}, "invalid_query"),
    ],
)
def test_search_rejects_out_of_policy_requests(built, kwargs, code):
    q = kwargs.pop("q")
    with pytest.raises(QueryError) as e:
        query.search(built, q, **kwargs)
    assert e.value.code == code


def test_get_book_fact_fields_only(built):
    book = query.get_book(built, ALMOND)
    assert book["title"] == "아몬드"
    assert book["contributors"] == [{"name": "손원평", "role": "author"}]
    assert {"scheme": "ksh", "code": "KSH2002030019", "label": None} in book["subjects"]
    assert book["sources"]["title"] == "lod"
    assert book["links"]["nlk_lod"] == "http://lod.nl.go.kr/resource/KJU201703899"
    assert not RICH_KEYS & set(book)
    allowed = set(query.PUBLIC_EDITION_FIELDS) | set(query.BOOK_EXTRA_FIELDS)
    assert set(book) <= allowed


def test_get_book_includes_rich_text_only_when_enabled(built):
    book = query.get_book(built, ALMOND, include_rich_text=True)
    assert book["rich_text"]["introduction"][0]["source"] == "nlseoji"


@pytest.mark.parametrize("raw", ["978-89-364-3426-7", "8936434268", " 9788936434267 "])
def test_get_book_accepts_isbn_forms(built, raw):
    assert query.get_book(built, raw)["isbn13"] == ALMOND


def test_get_book_invalid_isbn(built):
    with pytest.raises(QueryError) as e:
        query.get_book(built, "12345")
    assert e.value.code == "invalid_isbn"


def test_get_book_unknown_is_none(built):
    assert query.get_book(built, "9791180000027") is None


def test_takedown_hides_book_and_set_member(built):
    built.execute("INSERT INTO gold.takedown (isbn13, reason) VALUES (%s, 'test')", (ALMOND,))
    assert query.get_book(built, ALMOND) is None
    member = built.execute(
        "SELECT isbn13 FROM silver.set_member WHERE set_isbn13 = %s LIMIT 1", (TRIAL_SET,)
    ).fetchone()["isbn13"]
    built.execute("INSERT INTO gold.takedown (isbn13, reason) VALUES (%s, 'test')", (member,))
    assert member not in {m["isbn13"] for m in query.get_set(built, TRIAL_SET)["members"]}


def test_get_set(built):
    s = query.get_set(built, TRIAL_SET)
    assert s["set_isbn13"] == TRIAL_SET
    assert len(s["members"]) == 6
    assert s["members"] == sorted(s["members"], key=lambda m: m["isbn13"])


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://www.nl.go.kr/seoji/fu/ecip/x.jpg", "https://www.nl.go.kr/seoji/fu/ecip/x.jpg"),
        ("https://nl.go.kr/seoji/fu/ecip/x.jpg", "https://nl.go.kr/seoji/fu/ecip/x.jpg"),
        ("http://192.168.100.216/seoji/x.jpg", None),
        ("http://10.0.0.1/x.jpg", None),
        ("http://localhost/x.jpg", None),
        ("http://2130706433/x.jpg", None),
        ("https://0x7f.1/x.jpg", None),
        ("http://localhost./x.jpg", None),
        ("https://evil.example.com/x.jpg", None),
        ("https://user:pw@www.nl.go.kr/x.jpg", None),
        ("https://www.nl.go.kr:8443/x.jpg", None),
        ("https://WWW.NL.GO.KR/x.jpg", "https://www.nl.go.kr/x.jpg"),
        ("javascript:alert(1)", None),
        ("ftp://www.nl.go.kr/x.jpg", None),
        (None, None),
    ],
)
def test_public_cover_url(url, expected):
    assert query.public_cover_url(url) == expected


def test_meta(built):
    from seoji.config import Settings

    m = query.meta(built, Settings(database_url="", seoji_cert_key=None, contact="t@example.org"))
    assert m["contact"] == "t@example.org"
    assert "국립중앙도서관" in m["attribution"]
    assert m["limits"] == {"max_limit": 50, "max_offset": 1000}
    assert m["rich_text"] is False


def test_eight_terms_are_allowed(built):
    assert query.search(built, " ".join(["재판"] * 8))["items"]


@pytest.mark.parametrize("raw", ["9788936434267\x00", "\x00"])
def test_isbn_with_control_characters_is_invalid(built, raw):
    with pytest.raises(QueryError) as e:
        query.get_book(built, raw)
    assert e.value.code == "invalid_isbn"


def test_taken_down_set_is_hidden(built):
    built.execute("INSERT INTO gold.takedown (isbn13, reason) VALUES (%s, 'test')", (TRIAL_SET,))
    assert query.get_set(built, TRIAL_SET) is None
    member = built.execute(
        "SELECT isbn13 FROM silver.set_member WHERE set_isbn13 = %s LIMIT 1", (TRIAL_SET,)
    ).fetchone()["isbn13"]
    assert query.get_book(built, member)["sets"] == []


@pytest.mark.parametrize("q", [ALMOND, "978-89-364-3426-7", "8936434268", " 978 89 364 3426 7 "])
def test_search_by_isbn_returns_that_book(built, q):
    result = query.search(built, q)
    assert [i["isbn13"] for i in result["items"]] == [ALMOND]
    assert result["has_more"] is False
    assert set(result["items"][0]) == set(query.SEARCH_ITEM_FIELDS)


def test_search_by_unknown_isbn_is_empty(built):
    assert query.search(built, "9791180000027")["items"] == []


def test_search_by_isbn_respects_takedown_and_korean_only(built):
    foreign = built.execute(
        "SELECT isbn13 FROM silver.edition WHERE NOT is_korean LIMIT 1"
    ).fetchone()["isbn13"]
    assert query.search(built, foreign)["items"]
    assert query.search(built, foreign, korean_only=True)["items"] == []
    built.execute("INSERT INTO gold.takedown (isbn13, reason) VALUES (%s, 'test')", (ALMOND,))
    assert query.search(built, ALMOND)["items"] == []


def test_search_by_isbn_beyond_first_page_is_empty(built):
    assert query.search(built, ALMOND, offset=20)["items"] == []


def test_bad_checksum_digits_fall_back_to_text_search(built):
    assert query.search(built, "9788936434268")["items"] == []  # no title contains it
