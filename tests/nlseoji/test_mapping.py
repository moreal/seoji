from datetime import UTC, date, datetime

from seoji.model import CandidateRecord, InvalidIsbn
from seoji.nlseoji.mapping import map_seoji_doc
from tests.nlseoji.conftest import fixture

NOW = datetime(2026, 10, 22, tzinfo=UTC)


def docs():
    return fixture("page_20220509_p1.json")["docs"] + fixture("page_20220509_p2.json")["docs"]


def test_paper_book():
    c = map_seoji_doc(docs()[0], NOW)
    assert isinstance(c, CandidateRecord)
    assert (c.source, c.source_key, c.isbn13) == ("nlseoji", "9788936434267", "9788936434267")
    f = c.fields
    assert f["title"] == "아몬드"
    assert f["price_planned"] == 16800
    assert (f["width_mm"], f["height_mm"]) == (128, 188)
    assert (f["pub_date"], f["pub_date_precision"]) == (date(2022, 5, 9), "day")
    assert f["binding"] == "paper"
    assert f["deposit_yn"] is True
    assert f["page_count"] == 263
    assert f["series_title"] == "창비청소년문학"
    assert ("add_code", "43810", None) in c.subjects
    assert ("seoji_subject", "문학", "문학") in c.subjects
    assert c.rich_text["introduction"].startswith("감정을")
    assert "price_real" not in f
    assert c.observed_at == NOW


def test_invalid_isbn():
    assert map_seoji_doc(docs()[1], NOW) == InvalidIsbn("nlseoji", "9788936434268", "9788936434268")


def test_ebook_and_set():
    c = map_seoji_doc(docs()[2], NOW)
    assert c.fields["binding"] == "ebook"
    assert c.fields["deposit_yn"] is False
    assert c.fields["price_real"] == 8000
    assert (c.set_isbn13, c.set_expression) == ("9791180000003", "세트, 전2권.")
    assert [(p.name, p.role) for p in c.contributors] == [
        ("김가상", "author"),
        ("이번역", "translator"),
    ]


def test_missing_isbn_is_skipped():
    assert map_seoji_doc({"TITLE": "ISBN 없음", "EA_ISBN": ""}, NOW) is None
