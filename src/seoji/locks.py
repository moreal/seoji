"""Advisory lock that orders bronze writes against silver builds.

Bronze writers hold it shared for each writing transaction and stamp `changed_at` with
clock_timestamp(); silver builds hold it exclusively. A build therefore sees every bronze row
committed before it started, and any row written after it started carries a later timestamp
than the build's watermark.
"""

import psycopg

BRONZE_LOCK_KEY = 0x5E011


def lock_bronze_shared(conn: psycopg.Connection) -> None:
    conn.execute("SELECT pg_advisory_xact_lock_shared(%s)", (BRONZE_LOCK_KEY,))


def lock_bronze_exclusive(conn: psycopg.Connection) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (BRONZE_LOCK_KEY,))
