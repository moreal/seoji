from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def connect(url: str) -> psycopg.Connection:
    return psycopg.connect(url, autocommit=False, row_factory=dict_row)


def migrate(conn: psycopg.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply migrations not yet recorded in public.schema_migrations, in name order."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS public.schema_migrations ("
        " version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
    )
    applied = {r["version"] for r in conn.execute("SELECT version FROM public.schema_migrations")}
    done = []
    for path in sorted(migrations_dir.glob("[0-9][0-9][0-9]_*.sql")):
        if path.name in applied:
            continue
        conn.execute(path.read_text())
        conn.execute("INSERT INTO public.schema_migrations (version) VALUES (%s)", (path.name,))
        done.append(path.name)
    conn.commit()
    return done
