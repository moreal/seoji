from pathlib import Path

import pyoxigraph as ox
import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "lod"
SAMPLE_KR = FIXTURES / "sample_kr.rdf"
SAMPLE_FOREIGN = FIXTURES / "sample_foreign.rdf"
NLK = "http://lod.nl.go.kr/resource/"
TITLE = "http://purl.org/dc/terms/title"


def write_nt(path: Path, triples) -> Path:
    ox.serialize(triples, output=str(path), format=ox.RdfFormat.N_TRIPLES)
    return path


@pytest.fixture
def kr_triples():
    return list(ox.parse(path=str(SAMPLE_KR), format=ox.RdfFormat.RDF_XML))


@pytest.fixture
def make_nt(tmp_path, kr_triples):
    """Build an N-Triples variant of sample_kr: drop some resources, retitle one."""

    def make(name: str, *, drop: set[str] = frozenset(), retitle: dict[str, str] | None = None):
        out = []
        for t in kr_triples:
            uri = t.subject.value
            if uri in drop:
                continue
            if retitle and uri in retitle and t.predicate.value == TITLE:
                t = ox.Triple(t.subject, t.predicate, ox.Literal(retitle[uri]))
            out.append(t)
        return write_nt(tmp_path / name, out)

    return make
