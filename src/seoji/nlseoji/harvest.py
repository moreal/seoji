import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

import psycopg
from psycopg.types.json import Jsonb

from seoji.locks import lock_bronze_shared
from seoji.model import CandidateRecord, InvalidIsbn
from seoji.nlseoji.client import (
    SEOJI_URL,
    FatalSeojiError,
    PageSizeTooLarge,
    SeojiClient,
    SeojiError,
    SeojiPage,
)
from seoji.nlseoji.mapping import map_seoji_doc

SOURCE = "nlseoji"
MIN_PAGE_SIZE = 10
ALL_CURSOR = "nlseoji_all"


@dataclass
class HarvestStats:
    days: int = 0
    requests: int = 0
    records: int = 0
    changed: int = 0
    invalid: int = 0
    total_count: int = 0
    skipped: int = 0


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


def _store_page(conn: psycopg.Connection, page: SeojiPage, stats: HarvestStats) -> None:
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
        _store_page(conn, page, stats)
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


def _resume(conn: psycopg.Connection, page_size: int, restart: bool) -> tuple[int, int | None]:
    """Record offset to fetch first (the last committed page again) and the last known total."""
    row = conn.execute(
        "SELECT page_no, page_size, total_count FROM bronze.harvest_cursor WHERE name = %s",
        (ALL_CURSOR,),
    ).fetchone()
    if restart or row is None:
        return 0, None
    offset = (row["page_no"] - 1) * row["page_size"]
    return offset - offset % page_size, row["total_count"] or None


def _fetch_block(
    conn, client: SeojiClient, offset: int, size: int, total: int | None, stats: HarvestStats
) -> int | None:
    """Fetch records [offset, offset+size). A failing block is split tenfold down to single
    records; a single record that still fails is skipped and logged. Returns TOTAL_COUNT."""
    stats.requests += 1
    try:
        page = client.search(
            page_no=offset // size + 1, page_size=size, sort="INPUT_DATE", order_by="ASC"
        )
        if not page.docs and page.total_count == 0 and total and offset < total:
            raise SeojiError("empty", "empty page before the known end")
    except (PageSizeTooLarge, FatalSeojiError):
        raise
    except SeojiError as e:
        if size == 1:
            conn.execute(
                "INSERT INTO bronze.harvest_skip (name, record_offset, error_code, message)"
                " VALUES (%s, %s, %s, %s) ON CONFLICT (name, record_offset) DO UPDATE SET"
                " error_code = EXCLUDED.error_code, message = EXCLUDED.message,"
                " skipped_at = now()",
                (ALL_CURSOR, offset, e.code, e.message),
            )
            stats.skipped += 1
            return None
        sub = max(1, size // 10)
        for start in range(offset, offset + size, sub):
            if total is not None and start >= total:
                break
            total = _fetch_block(conn, client, start, sub, total, stats) or total
        return total
    _store_page(conn, page, stats)
    return page.total_count


def harvest_all(
    conn: psycopg.Connection,
    client: SeojiClient,
    *,
    page_size: int = 1000,
    restart: bool = False,
    max_pages: int | None = None,
    on_page: Callable[[int, int, int], None] | None = None,
) -> HarvestStats:
    """Page through every Seoji record by INPUT_DATE ascending, resuming from the cursor.

    New records sort to the end, so earlier pages stay put while a run is in progress, and a
    finished run can be repeated to pick up the tail.
    """
    stats = HarvestStats()
    offset, total = _resume(conn, page_size, restart)
    fetched = 0
    while max_pages is None or fetched < max_pages:
        lock_bronze_shared(conn)
        try:
            reported = _fetch_block(conn, client, offset, page_size, total, stats)
        except PageSizeTooLarge:
            conn.rollback()
            if page_size <= MIN_PAGE_SIZE:
                raise
            page_size = max(MIN_PAGE_SIZE, page_size // 2)
            offset -= offset % page_size
            continue
        if reported:
            total = reported
        page_no = offset // page_size + 1
        done = total is not None and page_no * page_size >= total
        conn.execute(
            "INSERT INTO bronze.harvest_cursor (name, page_no, page_size, total_count, updated_at,"
            " completed_at) VALUES (%(name)s, %(page)s, %(size)s, %(total)s, now(),"
            " CASE WHEN %(done)s THEN now() END)"
            " ON CONFLICT (name) DO UPDATE SET page_no = EXCLUDED.page_no,"
            " page_size = EXCLUDED.page_size, total_count = EXCLUDED.total_count,"
            " updated_at = EXCLUDED.updated_at, completed_at = EXCLUDED.completed_at",
            {"name": ALL_CURSOR, "page": page_no, "size": page_size, "total": total,
             "done": done},
        )  # fmt: skip
        conn.commit()
        stats.total_count = total or 0
        if on_page:
            on_page(page_no, page_size, total or 0)
        fetched += 1
        if done:
            break
        offset += page_size
    return stats
