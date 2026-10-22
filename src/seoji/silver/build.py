import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

import psycopg
from psycopg.types.json import Jsonb

from seoji.gold.build import rebuild_search_doc
from seoji.lod.mapping import map_lod_resource
from seoji.lod.parse import LodResource
from seoji.merge.merge import MergedEdition, merge_edition
from seoji.model import FIELDS, CandidateRecord, InvalidIsbn, NoIsbnRecord
from seoji.nlseoji.mapping import map_seoji_doc
from seoji.normalize.isbn import is_korean_isbn, isbn13_to_10
from seoji.normalize.text import compare_key

BATCH = 2000
REBUILT_TABLES = (
    "silver.candidate", "silver.edition", "silver.edition_record_link",
    "silver.manifestation_no_isbn", "silver.edition_contributor", "silver.book_set",
    "silver.set_member", "silver.edition_subject", "silver.edition_rich_text",
    "silver.field_provenance", "silver.merge_issue",
)  # fmt: skip
ADD_COLUMNS = ("add_reader", "add_form", "add_kdc_class", "add_kdc_division")
EDITION_COLUMNS = (
    "isbn13", "isbn10", "primary_resource_uri", *FIELDS, *ADD_COLUMNS, "title_normalized",
    "publisher_normalized", "pub_status", "is_korean", "provenance", "content_hash",
)  # fmt: skip
_TOTAL_VOLUMES = re.compile(r"전\s*(\d+)\s*권")


@dataclass
class BuildStats:
    candidates: int = 0
    editions: int = 0
    no_isbn: int = 0
    issues: int = 0


# ── mapping bronze → silver.candidate ─────────────────────────────────────────


def _write_mapped(
    conn: psycopg.Connection,
    cands: list[CandidateRecord],
    no_isbn: list[NoIsbnRecord],
    invalid: list[InvalidIsbn],
    stats: BuildStats,
) -> None:
    if cands:
        with conn.cursor().copy(
            "COPY silver.candidate (source, source_key, isbn13, body) FROM STDIN"
        ) as copy:
            for c in cands:
                copy.write_row((c.source, c.source_key, c.isbn13, Jsonb(c.to_json())))
    if no_isbn:
        conn.cursor().executemany(
            "INSERT INTO silver.manifestation_no_isbn VALUES (%s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (resource_uri) DO NOTHING",
            [(r.resource_uri, r.title, r.responsibility_stmt, r.publisher, r.issued_year, r.kdc)
             for r in no_isbn],
        )  # fmt: skip
    if invalid:
        conn.cursor().executemany(
            "INSERT INTO silver.merge_issue (kind, source, source_key, detail)"
            " VALUES ('invalid_isbn', %s, %s, %s)",
            [(i.source, i.source_key, Jsonb({"raw": i.raw})) for i in invalid],
        )
    stats.candidates += len(cands)
    stats.no_isbn += len(no_isbn)
    stats.issues += len(invalid)


def _map_lod(conn: psycopg.Connection, where: str, params: tuple, stats: BuildStats) -> set[str]:
    isbns: set[str] = set()
    with conn.cursor(name="lod_rows") as cur:
        cur.execute(f"SELECT resource_uri, body FROM bronze.lod_resource WHERE {where}", params)
        while rows := cur.fetchmany(BATCH):
            cands, no_isbn, invalid = [], [], []
            for row in rows:
                c, n, i = map_lod_resource(LodResource(row["resource_uri"], row["body"]))
                cands += c
                invalid += i
                if n:
                    no_isbn.append(n)
            _write_mapped(conn, cands, no_isbn, invalid, stats)
            isbns |= {c.isbn13 for c in cands}
    return isbns


def _map_nlseoji(
    conn: psycopg.Connection, where: str, params: tuple, stats: BuildStats
) -> set[str]:
    isbns: set[str] = set()
    with conn.cursor(name="nlseoji_rows") as cur:
        cur.execute(
            "SELECT record, changed_at FROM bronze.source_record"
            f" WHERE source = 'nlseoji' AND {where}",
            params,
        )
        while rows := cur.fetchmany(BATCH):
            cands, invalid = [], []
            for row in rows:
                mapped = map_seoji_doc(row["record"], row["changed_at"])
                if isinstance(mapped, CandidateRecord):
                    cands.append(mapped)
                elif isinstance(mapped, InvalidIsbn):
                    invalid.append(mapped)
            _write_mapped(conn, cands, [], invalid, stats)
            isbns |= {c.isbn13 for c in cands}
    return isbns


# ── merging silver.candidate → silver.edition and children ───────────────────


def _content_hash(m: MergedEdition) -> bytes:
    data = {
        "fields": m.fields,
        "pub_status": m.pub_status,
        "contributors": [(p.name, p.role, p.role_raw, s) for p, s in m.contributors],
        "subjects": sorted(m.subjects, key=str),
        "rich_text": sorted(m.rich_text),
        "sets": sorted(m.set_links, key=str),
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).digest()


def _edition_row(m: MergedEdition) -> tuple:
    f = m.fields
    title = f.get("title") or ""
    values = {
        "isbn13": m.isbn13,
        "isbn10": isbn13_to_10(m.isbn13),
        "primary_resource_uri": m.primary_resource_uri,
        **{name: f.get(name) for name in (*FIELDS, *ADD_COLUMNS)},
        "title": title,
        "title_normalized": compare_key(title),
        "publisher_normalized": compare_key(f.get("publisher")) or None,
        "pub_status": m.pub_status,
        "is_korean": is_korean_isbn(m.isbn13),
        "provenance": Jsonb({p.field: p.source for p in m.provenance if p.chosen}),
        "content_hash": _content_hash(m),
    }
    return tuple(values[c] for c in EDITION_COLUMNS)


def _copy(conn: psycopg.Connection, table: str, columns: Iterable[str], rows: list[tuple]):
    if not rows:
        return
    with conn.cursor().copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)


def _write_editions(conn: psycopg.Connection, merged: list[MergedEdition]) -> None:
    _copy(conn, "silver.edition", EDITION_COLUMNS, [_edition_row(m) for m in merged])
    _copy(
        conn,
        "silver.edition_record_link",
        ("isbn13", "source", "source_key", "link_role"),
        [(m.isbn13, *link) for m in merged for link in m.links],
    )
    _copy(
        conn, "silver.edition_contributor",
        ("isbn13", "ordinal", "name", "name_normalized", "role", "role_raw", "source"),
        [(m.isbn13, i, p.name, compare_key(p.name), p.role, p.role_raw, source)
         for m in merged for i, (p, source) in enumerate(m.contributors, 1)],
    )  # fmt: skip
    _copy(
        conn,
        "silver.edition_subject",
        ("isbn13", "scheme", "code", "label", "source"),
        [(m.isbn13, *s) for m in merged for s in m.subjects],
    )
    _copy(
        conn,
        "silver.edition_rich_text",
        ("isbn13", "kind", "source", "body", "redistributable"),
        [
            (m.isbn13, kind, source, body, False)
            for m in merged
            for kind, source, body in m.rich_text
        ],
    )
    _copy(
        conn, "silver.field_provenance",
        ("isbn13", "field", "source", "source_key", "raw_value", "chosen", "rule"),
        [(m.isbn13, p.field, p.source, p.source_key, p.raw_value, p.chosen, p.rule)
         for m in merged for p in m.provenance],
    )  # fmt: skip
    conn.cursor().executemany(
        "INSERT INTO silver.merge_issue (isbn13, kind, detail) VALUES (%s, %s, %s)",
        [(m.isbn13, i.kind, Jsonb(i.detail)) for m in merged for i in m.issues],
    )
    sets = {s[0]: s for m in merged for s in m.set_links}
    conn.cursor().executemany(
        "INSERT INTO silver.book_set (set_isbn13, set_add_code, set_expression, total_volumes,"
        " is_open_ended) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (set_isbn13) DO UPDATE SET"
        " set_add_code = COALESCE(EXCLUDED.set_add_code, silver.book_set.set_add_code),"
        " set_expression = COALESCE(EXCLUDED.set_expression, silver.book_set.set_expression),"
        " total_volumes = COALESCE(EXCLUDED.total_volumes, silver.book_set.total_volumes),"
        " is_open_ended = silver.book_set.is_open_ended AND EXCLUDED.is_open_ended",
        [(isbn, code, expr, total, total is None)
         for isbn, code, expr in sets.values()
         for total in [_total_volumes(expr)]],
    )  # fmt: skip
    _copy(
        conn, "silver.set_member", ("set_isbn13", "isbn13", "volume_label"),
        [(set_isbn, m.isbn13, m.fields.get("volume_label"))
         for m in merged for set_isbn, _, _ in m.set_links],
    )  # fmt: skip


def _total_volumes(expression: str | None) -> int | None:
    m = _TOTAL_VOLUMES.search(expression or "")
    return int(m.group(1)) if m else None


def _merge(conn: psycopg.Connection, isbns: list[str] | None) -> int:
    where, params = ("WHERE isbn13 = ANY(%s)", (isbns,)) if isbns is not None else ("", ())
    count = 0
    with conn.cursor(name="candidates") as cur:
        cur.execute(
            "SELECT isbn13, array_agg(body ORDER BY source, source_key) AS bodies"
            f" FROM silver.candidate {where} GROUP BY isbn13 ORDER BY isbn13",
            params,
        )
        while rows := cur.fetchmany(BATCH):
            merged = [
                merge_edition(r["isbn13"], [CandidateRecord.from_json(b) for b in r["bodies"]])
                for r in rows
            ]
            _write_editions(conn, merged)
            count += len(merged)
    conn.execute(
        "UPDATE silver.book_set b SET title = e.title FROM silver.edition e"
        " WHERE e.isbn13 = b.set_isbn13 AND b.title IS DISTINCT FROM e.title"
    )
    return count


# ── entry points ─────────────────────────────────────────────────────────────


def _start(conn: psycopg.Connection, kind: str) -> int:
    return conn.execute(
        "INSERT INTO silver.build_state (kind, started_at) VALUES (%s, now()) RETURNING id",
        (kind,),
    ).fetchone()["id"]


def _finish(conn: psycopg.Connection, state_id: int, stats: BuildStats) -> None:
    conn.execute(
        "UPDATE silver.build_state SET finished_at = clock_timestamp(), editions = %s"
        " WHERE id = %s",
        (stats.editions, state_id),
    )
    conn.commit()


def rebuild_silver(conn: psycopg.Connection, *, with_gold: bool = True) -> BuildStats:
    """Recompute every silver table from bronze."""
    stats = BuildStats()
    conn.execute(f"TRUNCATE {', '.join(REBUILT_TABLES)} RESTART IDENTITY")
    state_id = _start(conn, "rebuild")
    _map_lod(conn, "deleted_at IS NULL", (), stats)
    _map_nlseoji(conn, "true", (), stats)
    stats.editions = _merge(conn, None)
    _finish(conn, state_id, stats)
    if with_gold:
        rebuild_search_doc(conn)
    return stats


def refresh_silver(conn: psycopg.Connection, *, with_gold: bool = True) -> BuildStats:
    """Re-map bronze rows changed since the last finished build and re-merge their ISBNs."""
    last = conn.execute(
        "SELECT started_at FROM silver.build_state WHERE finished_at IS NOT NULL"
        " ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if last is None:
        return rebuild_silver(conn, with_gold=with_gold)
    since = last["started_at"]
    stats = BuildStats()
    state_id = _start(conn, "refresh")

    lod_keys = [
        r["resource_uri"]
        for r in conn.execute(
            "SELECT resource_uri FROM bronze.lod_resource WHERE changed_at >= %s", (since,)
        )
    ]
    seoji_keys = [
        r["source_key"]
        for r in conn.execute(
            "SELECT source_key FROM bronze.source_record"
            " WHERE source = 'nlseoji' AND changed_at >= %s",
            (since,),
        )
    ]
    affected: set[str] = set()
    for source, keys in (("lod", lod_keys), ("nlseoji", seoji_keys)):
        if not keys:
            continue
        affected |= {
            r["isbn13"]
            for r in conn.execute(
                "DELETE FROM silver.candidate WHERE source = %s AND source_key = ANY(%s)"
                " RETURNING isbn13",
                (source, keys),
            )
        }
        conn.execute(
            "DELETE FROM silver.merge_issue WHERE kind = 'invalid_isbn' AND source = %s"
            " AND source_key = ANY(%s)",
            (source, keys),
        )
    if lod_keys:
        conn.execute(
            "DELETE FROM silver.manifestation_no_isbn WHERE resource_uri = ANY(%s)", (lod_keys,)
        )
        affected |= _map_lod(
            conn, "resource_uri = ANY(%s) AND deleted_at IS NULL", (lod_keys,), stats
        )
    if seoji_keys:
        affected |= _map_nlseoji(conn, "source_key = ANY(%s)", (seoji_keys,), stats)

    isbns = sorted(affected)
    conn.execute("DELETE FROM silver.edition WHERE isbn13 = ANY(%s)", (isbns,))
    conn.execute(
        "DELETE FROM silver.merge_issue WHERE isbn13 = ANY(%s) AND kind <> 'invalid_isbn'",
        (isbns,),
    )
    stats.editions = _merge(conn, isbns)
    _finish(conn, state_id, stats)
    if with_gold and isbns:
        rebuild_search_doc(conn, isbns)
    return stats
