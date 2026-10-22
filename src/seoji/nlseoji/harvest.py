import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

import psycopg
from psycopg.types.json import Jsonb

from seoji.locks import lock_bronze_shared
from seoji.model import CandidateRecord, InvalidIsbn
from seoji.nlseoji.client import SEOJI_URL, PageSizeTooLarge, SeojiClient, SeojiPage
from seoji.nlseoji.mapping import map_seoji_doc

SOURCE = "nlseoji"
MIN_PAGE_SIZE = 10


@dataclass
class HarvestStats:
    days: int = 0
    requests: int = 0
    records: int = 0
    changed: int = 0
    invalid: int = 0


def _sha256(obj) -> bytes:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode()).digest()


def window_dates(name: Literal["daily", "weekly"], today: date) -> tuple[date, date]:
    if name == "daily":
        return today - timedelta(days=30), today + timedelta(days=90)
    return today - timedelta(days=365), today - timedelta(days=31)


def _store_payload(conn: psycopg.Connection, page: SeojiPage) -> int:
    sha = _sha256(page.raw)
    row = conn.execute(
        "INSERT INTO bronze.api_payload (source, endpoint, request_params, fetched_at,"
        " http_status, body, body_sha256) VALUES (%s, %s, %s, now(), 200, %s, %s)"
        " ON CONFLICT (source, body_sha256) DO NOTHING RETURNING id",
        (SOURCE, SEOJI_URL, Jsonb(page.params), Jsonb(page.raw), sha),
    ).fetchone()
    if row:
        return row["id"]
    return conn.execute(
        "SELECT id FROM bronze.api_payload WHERE source = %s AND body_sha256 = %s", (SOURCE, sha)
    ).fetchone()["id"]


def _store_record(conn, key: str, isbn13: str | None, doc: dict, payload_id: int) -> bool:
    """Upsert one doc; return True when it is new or its content changed."""
    sha = _sha256(doc)
    old = conn.execute(
        "SELECT record_sha256 FROM bronze.source_record WHERE source = %s AND source_key = %s",
        (SOURCE, key),
    ).fetchone()
    if old and bytes(old["record_sha256"]) == sha:
        conn.execute(
            "UPDATE bronze.source_record SET last_seen_at = now()"
            " WHERE source = %s AND source_key = %s",
            (SOURCE, key),
        )
        return False
    conn.execute(
        "INSERT INTO bronze.source_record (source, source_key, isbn13, payload_id, record,"
        " record_sha256, first_seen_at, last_seen_at, changed_at)"
        " VALUES (%s, %s, %s, %s, %s, %s, now(), now(), clock_timestamp())"
        " ON CONFLICT (source, source_key) DO UPDATE SET isbn13 = EXCLUDED.isbn13,"
        " payload_id = EXCLUDED.payload_id, record = EXCLUDED.record,"
        " record_sha256 = EXCLUDED.record_sha256, last_seen_at = now(),"
        " changed_at = clock_timestamp()",
        (SOURCE, key, isbn13, payload_id, Jsonb(doc), sha),
    )
    return True


def _harvest_day(conn, client: SeojiClient, day: date, page_size: int, stats: HarvestStats):
    ymd = day.strftime("%Y%m%d")
    lock_bronze_shared(conn)  # held until the day is committed
    page_no = 1
    while True:
        try:
            page = client.search(
                start_publish_date=ymd, end_publish_date=ymd, page_no=page_no, page_size=page_size
            )
        except PageSizeTooLarge:
            if page_size <= MIN_PAGE_SIZE:
                raise
            page_size, page_no = max(MIN_PAGE_SIZE, page_size // 2), 1
            stats.requests += 1
            continue
        stats.requests += 1
        payload_id = _store_payload(conn, page)
        now = datetime.now(UTC)
        for doc in page.docs:
            mapped = map_seoji_doc(doc, now)
            if mapped is None:  # no ISBN at all: keep it in bronze, keyed by content
                key, isbn13 = "sha:" + _sha256(doc).hex(), None
            elif isinstance(mapped, InvalidIsbn):
                stats.invalid += 1
                key, isbn13 = mapped.source_key, None
            else:
                assert isinstance(mapped, CandidateRecord)
                stats.records += 1
                key, isbn13 = mapped.source_key, mapped.isbn13
            stats.changed += _store_record(conn, key, isbn13, doc, payload_id)
        if not page.docs or page_no * page_size >= page.total_count:
            return
        page_no += 1


def harvest_range(
    conn: psycopg.Connection, client: SeojiClient, start: date, end: date, *, page_size: int = 100
) -> HarvestStats:
    stats = HarvestStats()
    day = start
    while day <= end:
        _harvest_day(conn, client, day, page_size, stats)
        conn.commit()
        stats.days += 1
        day += timedelta(days=1)
    return stats
