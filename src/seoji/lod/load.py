import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from seoji.locks import lock_bronze_shared
from seoji.lod.parse import Format, LodResource, body_hash, iter_resources, merge_bodies


@dataclass
class LoadStats:
    dump_id: int
    resources: int = 0
    inserted: int = 0
    changed: int = 0
    unchanged: int = 0
    tombstoned: int = 0


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _stage(conn: psycopg.Connection, batch: dict[str, LodResource], dump_id: int) -> None:
    """Write a batch into bronze.lod_stage, merging subjects already staged for this dump."""
    earlier = conn.execute(
        "SELECT resource_uri, body FROM bronze.lod_stage"
        " WHERE dump_id = %s AND resource_uri = ANY(%s)",
        (dump_id, list(batch)),
    ).fetchall()
    for row in earlier:
        res = batch[row["resource_uri"]]
        res.body = merge_bodies(row["body"], res.body)
    conn.execute(
        "CREATE TEMP TABLE IF NOT EXISTS tmp_lod"
        " (resource_uri text PRIMARY KEY, body jsonb, body_sha256 bytea) ON COMMIT DELETE ROWS"
    )
    with conn.cursor().copy("COPY tmp_lod (resource_uri, body, body_sha256) FROM STDIN") as copy:
        for res in batch.values():
            copy.write_row((res.uri, Jsonb(res.body), body_hash(res.body)))
    conn.execute(
        "INSERT INTO bronze.lod_stage (dump_id, resource_uri, body, body_sha256)"
        " SELECT %s, resource_uri, body, body_sha256 FROM tmp_lod"
        " ON CONFLICT (dump_id, resource_uri) DO UPDATE"
        " SET body = EXCLUDED.body, body_sha256 = EXCLUDED.body_sha256",
        (dump_id,),
    )
    conn.commit()
    batch.clear()


def _apply_stage(conn: psycopg.Connection, stats: LoadStats, dataset: str) -> None:
    """Move the staged dump into bronze.lod_resource in one transaction."""
    lock_bronze_shared(conn)
    counts = conn.execute(
        """
        SELECT count(*) AS resources,
               count(*) FILTER (WHERE r.resource_uri IS NULL) AS inserted,
               count(*) FILTER (WHERE r.body_sha256 = s.body_sha256 AND r.deleted_at IS NULL)
                 AS unchanged,
               count(*) FILTER (WHERE r.resource_uri IS NOT NULL
                 AND (r.body_sha256 <> s.body_sha256 OR r.deleted_at IS NOT NULL)) AS changed
          FROM bronze.lod_stage s LEFT JOIN bronze.lod_resource r USING (resource_uri)
         WHERE s.dump_id = %s
        """,
        (stats.dump_id,),
    ).fetchone()
    stats.resources = counts["resources"]
    stats.inserted = counts["inserted"]
    stats.unchanged = counts["unchanged"]
    stats.changed = counts["changed"]
    conn.execute(
        """
        INSERT INTO bronze.lod_resource AS r
          (resource_uri, dataset, body, body_sha256, first_dump_id, last_dump_id, changed_at)
        SELECT resource_uri, %(dataset)s, body, body_sha256, dump_id, dump_id, clock_timestamp()
          FROM bronze.lod_stage WHERE dump_id = %(dump)s
        ON CONFLICT (resource_uri) DO UPDATE SET
          body = EXCLUDED.body,
          body_sha256 = EXCLUDED.body_sha256,
          last_dump_id = EXCLUDED.last_dump_id,
          changed_at = CASE
            WHEN r.body_sha256 = EXCLUDED.body_sha256 AND r.deleted_at IS NULL THEN r.changed_at
            ELSE EXCLUDED.changed_at END,
          deleted_at = NULL
        """,
        {"dataset": dataset, "dump": stats.dump_id},
    )
    conn.execute("DELETE FROM bronze.lod_stage WHERE dump_id = %s", (stats.dump_id,))


def load_dump(
    conn: psycopg.Connection,
    path: Path,
    *,
    dataset: str,
    fmt: Format,
    dump_date: date | None,
    mark_missing: bool = False,
    batch_size: int = 5000,
) -> LoadStats:
    path = Path(path)
    dump_id = conn.execute(
        "INSERT INTO bronze.lod_dump (dataset, format, file_name, file_sha256, dump_date,"
        " downloaded_at) VALUES (%s, %s, %s, %s, %s, now()) RETURNING dump_id",
        (dataset, fmt, path.name, _file_sha256(path), dump_date),
    ).fetchone()["dump_id"]
    conn.commit()
    stats = LoadStats(dump_id)
    batch: dict[str, LodResource] = {}
    for res in iter_resources(path, fmt):
        if res.uri in batch:
            batch[res.uri].body = merge_bodies(batch[res.uri].body, res.body)
            continue
        batch[res.uri] = res
        if len(batch) >= batch_size:
            _stage(conn, batch, dump_id)
    if batch:
        _stage(conn, batch, dump_id)

    _apply_stage(conn, stats, dataset)

    if mark_missing:
        stats.tombstoned = conn.execute(
            "UPDATE bronze.lod_resource SET deleted_at = now(), changed_at = clock_timestamp()"
            " WHERE dataset = %s AND last_dump_id IS DISTINCT FROM %s AND deleted_at IS NULL",
            (dataset, dump_id),
        ).rowcount
    conn.execute(
        "UPDATE bronze.lod_dump SET resource_count = %s WHERE dump_id = %s",
        (stats.resources, dump_id),
    )
    conn.commit()
    return stats
