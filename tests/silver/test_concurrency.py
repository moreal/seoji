import threading
import time
from datetime import date

from psycopg.types.json import Jsonb

from seoji.db import connect
from seoji.locks import lock_bronze_exclusive, lock_bronze_shared
from seoji.lod.load import load_dump
from seoji.nlseoji.harvest import harvest_range
from seoji.silver.build import rebuild_silver, refresh_silver
from tests.lod_helpers import SAMPLE_KR
from tests.seoji_helpers import fixture, paged_handler

EBOOK = fixture("page_20220509_p2.json")["docs"][0]


def _run(fn) -> threading.Thread:
    t = threading.Thread(target=fn, daemon=True)
    t.start()
    time.sleep(0.4)
    return t


def test_refresh_waits_for_inflight_bronze_writer(db, migrated_url):
    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    rebuild_silver(db)
    with connect(migrated_url) as writer:
        lock_bronze_shared(writer)
        writer.execute(
            "INSERT INTO bronze.source_record (source, source_key, isbn13, record, record_sha256,"
            " first_seen_at, last_seen_at, changed_at) VALUES ('nlseoji', %s, %s, %s, %s, now(),"
            " now(), clock_timestamp())",
            ("9791180000010", "9791180000010", Jsonb(EBOOK), b"x"),
        )
        refresher = _run(lambda: refresh_silver(db))
        assert refresher.is_alive(), "refresh must wait for the in-flight bronze write"
        writer.commit()
    refresher.join(10)
    row = db.execute("SELECT 1 AS ok FROM silver.edition WHERE isbn13 = '9791180000010'").fetchone()
    assert row is not None


def test_harvest_waits_for_running_refresh(db, migrated_url, make_client):
    client, _, _ = make_client(paged_handler)
    with connect(migrated_url) as holder:
        lock_bronze_exclusive(holder)
        harvester = _run(
            lambda: harvest_range(db, client, date(2022, 5, 9), date(2022, 5, 9), page_size=2)
        )
        assert harvester.is_alive(), "bronze writes must wait while silver is being built"
        released_at = holder.execute("SELECT clock_timestamp() AS t").fetchone()["t"]
        holder.commit()
    harvester.join(10)
    rows = db.execute("SELECT changed_at FROM bronze.source_record").fetchall()
    assert rows and all(r["changed_at"] > released_at for r in rows)
