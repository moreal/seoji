"""Mapping checks against real Seoji docs (tests/fixtures/nlseoji/real_20220509_sample.json)."""

from datetime import UTC, date, datetime

import pytest

from seoji.model import CandidateRecord
from seoji.nlseoji.mapping import map_seoji_doc
from seoji.normalize.authors import Contributor
from tests.seoji_helpers import fixture

NOW = datetime(2026, 10, 22, tzinfo=UTC)
DOCS = {d["_case"]: d for d in fixture("real_20220509_sample.json")["docs"]}


def mapped(case: str) -> CandidateRecord:
    c = map_seoji_doc(DOCS[case], NOW)
    assert isinstance(c, CandidateRecord), case
    return c


@pytest.mark.parametrize("case", sorted(DOCS))
def test_every_real_doc_maps(case):
    mapped(case)


def test_paper_deposited():
    f = mapped("paper_deposited").fields
    assert (f["pub_date"], f["pub_date_precision"]) == (date(2022, 5, 9), "day")
    assert (f["binding"], f["price_planned"], f["deposit_yn"]) == ("paper", 14000, True)


def test_real_publish_date_preferred_over_planned():
    doc = DOCS["paper_deposited"] | {"PUBLISH_PREDATE": "20220501", "REAL_PUBLISH_DATE": "20220512"}
    assert map_seoji_doc(doc, NOW).fields["pub_date"] == date(2022, 5, 12)


def test_set_only_record_becomes_set_isbn_candidate():
    c = mapped("set_record")
    assert (c.isbn13, c.source_key, c.set_isbn13) == ("9791169031547", "9791169031547", None)
    assert c.set_expression == "전6권"
    assert c.fields["ea_add_code"] == "05810"


def test_set_member_points_at_set():
    assert mapped("set_member").set_isbn13 == "9791169031547"


def test_audio_book_binding():
    assert mapped("audio").fields["binding"] == "audio"


def test_illustrator_role_word():
    assert mapped("illustrator_role").contributors == [
        Contributor("Kelly Jang", "author", "저자"),
        Contributor("송길성", "illustrator", "삽화가(그림작가)"),
    ]


def test_non_sale_price_is_empty():
    assert "price_planned" not in mapped("non_sale").fields
