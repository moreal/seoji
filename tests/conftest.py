import os
import uuid

import psycopg
import pytest
from psycopg import sql

from seoji.db import connect, migrate

ADMIN_URL = os.environ.get(
    "SEOJI_TEST_ADMIN_URL", "postgresql://seoji:seoji@localhost:55432/postgres"
)


def _url_for(dbname: str) -> str:
    base, _, _ = ADMIN_URL.rpartition("/")
    return f"{base}/{dbname}"


@pytest.fixture(scope="session")
def db_url():
    name = f"seoji_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    yield _url_for(name)
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture(scope="session")
def migrated_url(db_url):
    with connect(db_url) as conn:
        migrate(conn)
    return db_url


@pytest.fixture
def db(migrated_url):
    with connect(migrated_url) as conn:
        tables = conn.execute(
            "SELECT format('%I.%I', schemaname, tablename) AS t FROM pg_tables "
            "WHERE schemaname IN ('bronze', 'silver', 'gold')"
        ).fetchall()
        if tables:
            conn.execute(f"TRUNCATE {', '.join(r['t'] for r in tables)} RESTART IDENTITY CASCADE")
            conn.commit()
        yield conn
