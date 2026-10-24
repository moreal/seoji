from datetime import date

from seoji.merge.merge import choose_primary_lod, choose_pub_date, merge_edition
from seoji.model import CandidateRecord
from seoji.normalize.authors import Contributor

ISBN = "9788936434267"


def lod(key="http://lod.nl.go.kr/resource/A", **fields):
    return CandidateRecord("lod", key, ISBN, fields=fields)


def seoji(**fields):
    return CandidateRecord("nlseoji", ISBN, ISBN, fields=fields)


def test_lod_wins_title_seoji_wins_price():
    m = merge_edition(ISBN, [lod(title="아몬드"), seoji(title="아몬드(양장)", price_real=12000)])
    assert m.fields["title"] == "아몬드"
    assert m.fields["price_real"] == 12000
    title_rows = [p for p in m.provenance if p.field == "title"]
    assert len(title_rows) == 2
    assert [p.source for p in title_rows if p.chosen] == ["lod"]
    assert next(p for p in title_rows if p.chosen).rule == "precedence:lod"


def test_invalid_value_falls_through():
    m = merge_edition(ISBN, [lod(title="x", page_count=0), seoji(page_count=263)])
    assert m.fields["page_count"] == 263


def test_false_boolean_is_a_value():
    m = merge_edition(ISBN, [seoji(title="x", deposit_yn=False)])
    assert m.fields["deposit_yn"] is False


def test_pub_date_deposited_and_year_matches():
    lod_c = lod(pub_date=date(2017, 1, 1), pub_date_precision="year")
    s = seoji(pub_date=date(2017, 3, 20), pub_date_precision="day", deposit_yn=True)
    assert choose_pub_date(lod_c, s) == (date(2017, 3, 20), "day", "seoji_deposited_match")


def test_pub_date_not_deposited_uses_lod():
    lod_c = lod(pub_date=date(2017, 1, 1), pub_date_precision="year")
    s = seoji(pub_date=date(2017, 3, 20), pub_date_precision="day", deposit_yn=False)
    assert choose_pub_date(lod_c, s) == (date(2017, 1, 1), "year", "lod")


def test_pub_date_seoji_only_is_announced():
    s = seoji(title="x", pub_date=date(2027, 1, 5), pub_date_precision="day", deposit_yn=False)
    assert choose_pub_date(None, s) == (date(2027, 1, 5), "day", "seoji_announced")
    m = merge_edition(ISBN, [s])
    assert m.pub_status == "announced"
    assert (m.fields["pub_date"], m.fields["pub_date_precision"]) == (date(2027, 1, 5), "day")


def test_lod_present_means_published():
    assert merge_edition(ISBN, [lod(title="x")]).pub_status == "published"


def test_multi_lod_picks_richer_and_flags():
    rich = lod(
        "http://lod.nl.go.kr/resource/B",
        title="t",
        publisher="p",
        kdc="8",
        page_count=1,
        language="kor",
    )
    thin = lod("http://lod.nl.go.kr/resource/A", title="t2", publisher="q")
    assert choose_primary_lod([thin, rich]) is rich
    m = merge_edition(ISBN, [thin, rich])
    assert m.primary_resource_uri == rich.source_key
    assert ("lod", thin.source_key, "secondary") in m.links
    assert ("lod", rich.source_key, "primary") in m.links
    assert m.fields["title"] == "t"
    assert [i.kind for i in m.issues] == ["multi_lod"]


def test_isbn_conflict_flagged():
    m = merge_edition(
        ISBN,
        [
            lod(title="아몬드", publisher="창비"),
            seoji(title="점자 교본", publisher="부산점자도서관"),
        ],
    )
    assert [i.kind for i in m.issues] == ["isbn_conflict"]
    assert m.fields["title"] == "아몬드"


def test_similar_titles_do_not_conflict():
    m = merge_edition(
        ISBN, [lod(title="아몬드", publisher="창비"), seoji(title="아몬드", publisher="창비")]
    )
    assert m.issues == []


def test_contributors_not_mixed():
    a = lod(title="x")
    a.contributors = [Contributor("손원평", "author", "지은이")]
    b = seoji(title="x")
    b.contributors = [
        Contributor("손원평", "author", "지음"),
        Contributor("누군가", "editor", "편"),
    ]
    m = merge_edition(ISBN, [a, b])
    assert m.contributors == [(Contributor("손원평", "author", "지은이"), "lod")]


def test_contributors_fall_back_to_seoji():
    b = seoji(title="x")
    b.contributors = [Contributor("손원평", "author", "지음")]
    m = merge_edition(ISBN, [lod(title="x"), b])
    assert m.contributors == [(Contributor("손원평", "author", "지음"), "nlseoji")]


def test_add_code_decoded():
    m = merge_edition(ISBN, [seoji(title="x", ea_add_code="43810")])
    assert m.fields["add_reader"] == "4"
    assert m.fields["add_form"] == "3"
    assert m.fields["add_kdc_class"] == "8"
    assert m.fields["add_kdc_division"] == "81"


def test_subjects_rich_text_and_sets_are_unioned():
    a = lod(title="x")
    a.subjects = [("kdc", "813.7", None)]
    a.rich_text = {"toc": "1장"}
    b = seoji(title="x")
    b.subjects = [("kdc", "813.7", None), ("add_code", "43810", None)]
    b.rich_text = {"introduction": "소개"}
    b.set_isbn13, b.set_expression = "9791180000003", "세트, 전2권."
    m = merge_edition(ISBN, [a, b])
    assert ("kdc", "813.7", None, "lod") in m.subjects
    assert ("kdc", "813.7", None, "nlseoji") in m.subjects
    assert ("toc", "lod", "1장") in m.rich_text
    assert m.set_links == [("9791180000003", None, "세트, 전2권.")]


def test_rich_text_only_from_primary_lod():
    a = lod("http://lod.nl.go.kr/resource/A", title="t", publisher="p")
    a.rich_text = {"toc": "primary"}
    b = lod("http://lod.nl.go.kr/resource/B", title="t")
    b.rich_text = {"toc": "secondary"}
    m = merge_edition(ISBN, [a, b])
    assert m.rich_text == [("toc", "lod", "primary")]


def test_absurd_numbers_are_rejected():
    m = merge_edition(
        ISBN,
        [
            seoji(
                title="x",
                price_planned=1_000_000_000_000_000,
                price_real=12000,
                width_mm=99999,
                height_mm=0,
                page_count=263,
            )
        ],
    )
    assert "price_planned" not in m.fields
    assert m.fields["price_real"] == 12000
    assert "width_mm" not in m.fields
    assert m.fields["page_count"] == 263


def test_every_int_column_value_fits_postgres_int():
    from seoji.merge.rules import is_valid

    for name in ("price_planned", "price_real", "page_count", "width_mm", "height_mm", "volumes"):
        assert not is_valid(name, 2**31), name
    assert not is_valid("height_cm", 10_000.0)
