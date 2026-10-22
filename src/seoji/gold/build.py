import psycopg

_SELECT = """
SELECT e.isbn13, e.title, c.authors, e.publisher, e.series_title, e.kdc, e.add_reader, e.binding,
       extract(year FROM e.pub_date)::int, e.is_korean,
       gold.search_key(concat_ws(' ', e.title, e.title, e.remainder_of_title, e.title_hanja,
                                 e.volume_label, c.authors, e.publisher, e.series_title,
                                 s.labels))
  FROM silver.edition e
  LEFT JOIN LATERAL (
    SELECT string_agg(name, ', ' ORDER BY first_ordinal) AS authors
      FROM (SELECT name, min(ordinal) AS first_ordinal FROM silver.edition_contributor
             WHERE isbn13 = e.isbn13 GROUP BY name) names
  ) c ON true
  LEFT JOIN LATERAL (
    SELECT string_agg(DISTINCT label, ' ') AS labels FROM silver.edition_subject
     WHERE isbn13 = e.isbn13 AND label IS NOT NULL
  ) s ON true
"""
_INSERT = (
    "INSERT INTO gold.search_doc (isbn13, title, authors, publisher, series_title, kdc,"
    " add_reader, binding, pub_year, is_korean, search_text) "
)


def rebuild_search_doc(conn: psycopg.Connection, isbns: list[str] | None = None) -> int:
    """Rebuild search documents for the given ISBNs, or all of them when isbns is None."""
    if isbns is None:
        conn.execute("TRUNCATE gold.search_doc")
        count = conn.execute(_INSERT + _SELECT).rowcount
    else:
        conn.execute("DELETE FROM gold.search_doc WHERE isbn13 = ANY(%s)", (isbns,))
        count = conn.execute(_INSERT + _SELECT + " WHERE e.isbn13 = ANY(%s)", (isbns,)).rowcount
    conn.commit()
    return count
