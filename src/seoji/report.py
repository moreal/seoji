import psycopg
from psycopg import sql

from seoji.model import FIELDS


def fill_rates(conn: psycopg.Connection) -> list[tuple[str, int, float]]:
    """Per FIELDS column of silver.edition: (field, non-empty rows, share of all rows)."""
    counts = sql.SQL(", ").join(
        sql.SQL("count(*) FILTER (WHERE {c} IS NOT NULL AND {c}::text <> '') AS {c}").format(
            c=sql.Identifier(f)
        )
        for f in FIELDS
    )
    row = conn.execute(
        sql.SQL("SELECT count(*) AS total, {} FROM silver.edition").format(counts)
    ).fetchone()
    total = row["total"]
    return [(f, row[f], row[f] / total if total else 0.0) for f in FIELDS]


def issue_counts(conn: psycopg.Connection) -> dict[str, int]:
    return {
        r["kind"]: r["n"]
        for r in conn.execute(
            "SELECT kind, count(*) AS n FROM silver.merge_issue WHERE resolved_at IS NULL"
            " GROUP BY kind ORDER BY kind"
        )
    }


def source_coverage(conn: psycopg.Connection) -> dict[str, int]:
    row = conn.execute(
        """
        SELECT count(*) FILTER (WHERE has_lod AND NOT has_seoji) AS lod_only,
               count(*) FILTER (WHERE has_seoji AND NOT has_lod) AS nlseoji_only,
               count(*) FILTER (WHERE has_lod AND has_seoji) AS both
          FROM (SELECT bool_or(source = 'lod') AS has_lod, bool_or(source = 'nlseoji') AS has_seoji
                  FROM silver.edition_record_link GROUP BY isbn13) per_edition
        """
    ).fetchone()
    return {k: row[k] for k in ("lod_only", "nlseoji_only", "both")}
