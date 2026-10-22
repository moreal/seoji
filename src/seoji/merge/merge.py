from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from seoji.merge.rules import PRECEDENCE, is_valid
from seoji.model import CandidateRecord
from seoji.normalize.addcode import decode_add_code
from seoji.normalize.authors import Contributor
from seoji.normalize.text import compare_key

CONFLICT_SIMILARITY = 0.3


@dataclass
class ProvenanceRow:
    field: str
    source: str
    source_key: str
    raw_value: str | None
    chosen: bool
    rule: str


@dataclass
class MergeIssue:
    kind: Literal["isbn_conflict", "multi_lod"]
    detail: dict


@dataclass
class MergedEdition:
    isbn13: str
    fields: dict[str, Any]
    pub_status: Literal["announced", "published"]
    primary_resource_uri: str | None
    links: list[tuple[str, str, str]] = field(default_factory=list)
    contributors: list[tuple[Contributor, str]] = field(default_factory=list)
    subjects: list[tuple[str, str, str | None, str]] = field(default_factory=list)
    rich_text: list[tuple[str, str, str]] = field(default_factory=list)
    set_links: list[tuple[str, str | None, str | None]] = field(default_factory=list)
    provenance: list[ProvenanceRow] = field(default_factory=list)
    issues: list[MergeIssue] = field(default_factory=list)


def choose_primary_lod(cands: list[CandidateRecord]) -> CandidateRecord:
    return min(cands, key=lambda c: (-len(c.fields), c.source_key))


def choose_pub_date(
    lod: CandidateRecord | None, seoji: CandidateRecord | None
) -> tuple[date | None, str | None, str]:
    def get(c):
        if c is None or not is_valid("pub_date", c.fields.get("pub_date")):
            return None, None
        return c.fields["pub_date"], c.fields.get("pub_date_precision")

    lod_date, lod_precision = get(lod)
    seoji_date, seoji_precision = get(seoji)
    deposited = seoji is not None and seoji.fields.get("deposit_yn") is True
    if deposited and lod_date and seoji_date and lod_date.year == seoji_date.year:
        return seoji_date, seoji_precision, "seoji_deposited_match"
    if lod_date:
        return lod_date, lod_precision, "lod"
    if seoji_date:
        return seoji_date, seoji_precision, "seoji_deposited" if deposited else "seoji_announced"
    return None, None, "none"


def _bigram_jaccard(a: str, b: str) -> float:
    ga = {a[i : i + 2] for i in range(len(a) - 1)} or {a}
    gb = {b[i : i + 2] for i in range(len(b) - 1)} or {b}
    return len(ga & gb) / len(ga | gb)


def _conflict(lod: CandidateRecord, seoji: CandidateRecord) -> MergeIssue | None:
    lt, st = lod.fields.get("title"), seoji.fields.get("title")
    lp, sp = lod.fields.get("publisher"), seoji.fields.get("publisher")
    if not (lt and st):
        return None
    if _bigram_jaccard(compare_key(lt), compare_key(st)) >= CONFLICT_SIMILARITY:
        return None
    if compare_key(lp) == compare_key(sp):
        return None
    return MergeIssue(
        "isbn_conflict",
        {"lod_title": lt, "seoji_title": st, "lod_publisher": lp, "seoji_publisher": sp},
    )


def merge_edition(isbn13: str, cands: list[CandidateRecord]) -> MergedEdition:
    lods = [c for c in cands if c.source == "lod"]
    seojis = [c for c in cands if c.source == "nlseoji"]
    primary = choose_primary_lod(lods) if lods else None
    seoji = seojis[0] if seojis else None
    by_source = {c.source: c for c in (primary, seoji) if c is not None}

    merged = MergedEdition(
        isbn13=isbn13,
        fields={},
        pub_status="published"
        if primary or (seoji and seoji.fields.get("deposit_yn") is True)
        else "announced",
        primary_resource_uri=primary.source_key if primary else None,
    )
    for c in cands:
        role = "secondary" if c.source == "lod" and c is not primary else "primary"
        merged.links.append((c.source, c.source_key, role))
    if len(lods) > 1:
        merged.issues.append(MergeIssue("multi_lod", {"uris": sorted(c.source_key for c in lods)}))

    def record(name: str, chosen_source: str | None, rule: str) -> None:
        for c in cands:
            if name in c.fields:
                chosen = c.source == chosen_source and (c is primary or c.source != "lod")
                merged.provenance.append(
                    ProvenanceRow(name, c.source, c.source_key, str(c.fields[name]), chosen, rule)
                )

    for name, order in PRECEDENCE.items():
        winner = next(
            (s for s in order if s in by_source and is_valid(name, by_source[s].fields.get(name))),
            None,
        )
        if winner:
            merged.fields[name] = by_source[winner].fields[name]
        record(name, winner, f"precedence:{winner}")

    pub_date, precision, rule = choose_pub_date(primary, seoji)
    if pub_date:
        merged.fields["pub_date"], merged.fields["pub_date_precision"] = pub_date, precision
    date_source = "lod" if rule == "lod" else "nlseoji" if rule.startswith("seoji") else None
    record("pub_date", date_source, rule)

    if decoded := decode_add_code(merged.fields.get("ea_add_code")):
        merged.fields |= {
            "add_reader": decoded.reader,
            "add_form": decoded.form,
            "add_kdc_class": decoded.kdc_class,
            "add_kdc_division": decoded.kdc_division,
        }

    for source in PRECEDENCE["responsibility_stmt"]:
        if source in by_source and by_source[source].contributors:
            merged.contributors = [(p, source) for p in by_source[source].contributors]
            break

    seen_subjects: set = set()
    seen_sets: set = set()
    for c in cands:
        for scheme, code, label in c.subjects:
            key = (scheme, code, label, c.source)
            if key not in seen_subjects:
                seen_subjects.add(key)
                merged.subjects.append(key)
        if c is primary or c is seoji:
            merged.rich_text += [(kind, c.source, body) for kind, body in c.rich_text.items()]
        if c.set_isbn13 and c.set_isbn13 not in seen_sets:
            seen_sets.add(c.set_isbn13)
            merged.set_links.append((c.set_isbn13, c.set_add_code, c.set_expression))

    if primary and seoji and (issue := _conflict(primary, seoji)):
        merged.issues.append(issue)
    return merged
