import uuid

import psycopg
from psycopg import sql

from seoji.db import connect, migrate
from tests.conftest import ADMIN_URL, _url_for


def test_migrate_applies_all_then_nothing():
    name = f"seoji_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    try:
        with connect(_url_for(name)) as conn:
            first = migrate(conn)
            assert first[0] == "001_bronze.sql"
            assert migrate(conn) == []
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


def test_extensions_and_schemas(db):
    exts = {r["extname"] for r in db.execute("SELECT extname FROM pg_extension")}
    assert {"pg_bigm", "pg_trgm"} <= exts
    schemas = {
        r["schema_name"] for r in db.execute("SELECT schema_name FROM information_schema.schemata")
    }
    assert {"bronze", "silver", "gold"} <= schemas
