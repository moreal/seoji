from datetime import date

import pytest

from seoji.lod.mapping import map_lod_resource
from seoji.lod.parse import iter_resources
from seoji.model import CandidateRecord, InvalidIsbn, NoIsbnRecord
from seoji.normalize.authors import Contributor
from seoji.normalize.isbn import is_korean_isbn
from tests.lod.conftest import NLK, SAMPLE_FOREIGN, SAMPLE_KR


@pytest.fixture(scope="module")
def mapped():
    out = {}
    for path in (SAMPLE_KR, SAMPLE_FOREIGN):
        for res in iter_resources(path, "rdfxml"):
            out[res.uri.removeprefix(NLK)] = map_lod_resource(res)
    return out


def by_isbn(cands: list[CandidateRecord]) -> dict[str, CandidateRecord]:
    return {c.isbn13: c for c in cands}


def test_almond(mapped):
    cands, no_isbn, invalid = mapped["KJU201703899"]
    assert no_isbn is None and invalid == []
    [c] = cands
    assert c.source == "lod" and c.source_key == NLK + "KJU201703899"
    assert c.isbn13 == "9788936434267"
    f = c.fields
    assert f["title"] == "아몬드"
    assert f["remainder_of_title"] == "손원평 장편소설"
    assert c.contributors == [Contributor("손원평", "author", "지은이")]
    assert f["publisher"] == "창비"
    assert (f["pub_date"], f["pub_date_precision"]) == (date(2017, 1, 1), "year")
    assert (f["page_count"], f["height_cm"]) == (263, 20.0)
    assert f["kdc"] == "813.7"
    assert f["nlk_call_no"] == "813.7-17-222"
    assert f["language"] == "kor"
    assert ("ksh", "KSH2002030019", None) in c.subjects
    assert ("kdc", "813.7", None) in c.subjects


def test_single_isbn_with_set(mapped):
    cands = by_isbn(mapped["KJU201108521"][0])
    assert set(cands) == {"9788926318874", "9791189431907"}
    assert cands["9788926318874"].set_isbn13 == "9791189431907"
    assert cands["9791189431907"].set_isbn13 is None


def test_lowercase_set_qualifier(mapped):
    cands = by_isbn(mapped["KJU201208224"][0])
    others = [c for isbn, c in cands.items() if isbn != "9788961596749"]
    assert others and all(c.set_isbn13 == "9788961596749" for c in others)


def test_volume_label_from_qualifier(mapped):
    cands = by_isbn(mapped["KJU200801614"][0])
    assert cands["9788925807164"].fields["volume_label"] == "제4권"


def test_multi_isbn_resource_shares_title(mapped):
    cands = mapped["KJU201211257"][0]
    assert len(cands) == 7
    assert {c.fields["title"] for c in cands} == {"(바로미와 함께하는) 좌충우돌 재판이야기"}
    labels = {c.fields.get("volume_label") for c in cands if c.isbn13 != "9788993171440"}
    assert None not in labels and len(labels) == 6


def test_no_isbn_resource(mapped):
    cands, no_isbn, invalid = mapped["CMO000000001"]
    assert cands == [] and invalid == []
    assert isinstance(no_isbn, NoIsbnRecord)
    assert no_isbn.resource_uri == NLK + "CMO000000001"
    assert (no_isbn.title, no_isbn.responsibility_stmt) == ("圖書館學論叢", "王振鵠 著")
    assert no_isbn.issued_year == 1984


def test_invalid_isbn_reported(mapped):
    cands, no_isbn, invalid = mapped["CMO000000042"]
    assert cands == [] and no_isbn is None
    assert invalid == [InvalidIsbn("lod", NLK + "CMO000000042", "9579005062(平裝)")]


def test_foreign_isbns_are_mapped(mapped):
    foreign = [
        c for key, (cands, _, _) in mapped.items() if key.startswith("CMO0000000") for c in cands
    ]
    assert any(not is_korean_isbn(c.isbn13) for c in foreign)


def test_candidate_json_roundtrip(mapped):
    [c] = mapped["KJU201703899"][0]
    assert CandidateRecord.from_json(c.to_json()) == c
