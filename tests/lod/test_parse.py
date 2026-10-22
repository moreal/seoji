from seoji.lod.parse import body_hash, iter_resources
from tests.lod_helpers import NLK, SAMPLE_KR

ISBN = "http://purl.org/ontology/bibo/isbn"
SUBJECT = "http://purl.org/dc/terms/subject"


def test_iter_resources_groups_by_subject():
    resources = {r.uri: r for r in iter_resources(SAMPLE_KR, "rdfxml")}
    assert len(resources) == 9
    almond = resources[NLK + "KJU201703899"].body
    assert almond[ISBN] == ["9788936434267"]
    assert {"@id": NLK + "KSH2002030019"} in almond[SUBJECT]


def test_body_hash_is_order_independent():
    a = {"p1": ["x", "y"], "p2": [{"@id": "u"}]}
    b = {"p2": [{"@id": "u"}], "p1": ["y", "x"]}
    assert body_hash(a) == body_hash(b)
