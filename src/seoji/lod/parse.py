import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pyoxigraph as ox

Format = Literal["ttl", "nt", "rdfxml", "jsonld"]
FORMATS: dict[str, ox.RdfFormat] = {
    "ttl": ox.RdfFormat.TURTLE,
    "nt": ox.RdfFormat.N_TRIPLES,
    "rdfxml": ox.RdfFormat.RDF_XML,
    "jsonld": ox.RdfFormat.JSON_LD,
}

Value = str | dict[str, str]


@dataclass
class LodResource:
    uri: str
    body: dict[str, list[Value]] = field(default_factory=dict)


def _value(term) -> Value:
    if isinstance(term, ox.Literal):
        if term.language:
            return {"@value": term.value, "@language": term.language}
        return term.value
    return {"@id": term.value}


def _sort_key(v: Value) -> str:
    return v if isinstance(v, str) else json.dumps(v, sort_keys=True, ensure_ascii=False)


def canonical(body: dict[str, list[Value]]) -> dict[str, list[Value]]:
    """Deduplicate and sort each predicate's values so equal content hashes equally."""
    out = {}
    for pred in sorted(body):
        seen = {_sort_key(v): v for v in body[pred]}
        out[pred] = [seen[k] for k in sorted(seen)]
    return out


def merge_bodies(a: dict[str, list[Value]], b: dict[str, list[Value]]) -> dict[str, list[Value]]:
    merged = {p: list(vs) for p, vs in a.items()}
    for p, vs in b.items():
        merged.setdefault(p, []).extend(vs)
    return canonical(merged)


def body_hash(body: dict[str, list[Value]]) -> bytes:
    data = json.dumps(canonical(body), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode()).digest()


def iter_resources(path: Path, fmt: Format) -> Iterator[LodResource]:
    """Stream triples and yield one resource per contiguous run of the same subject."""
    current: LodResource | None = None
    for triple in ox.parse(path=str(path), format=FORMATS[fmt]):
        uri = triple.subject.value
        if current is None or current.uri != uri:
            if current is not None:
                current.body = canonical(current.body)
                yield current
            current = LodResource(uri)
        current.body.setdefault(triple.predicate.value, []).append(_value(triple.object))
    if current is not None:
        current.body = canonical(current.body)
        yield current
