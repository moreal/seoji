-- ISBNs hidden from every public channel (web, REST API, MCP) after a takedown request.
CREATE TABLE gold.takedown (
  isbn13     char(13) PRIMARY KEY,
  reason     text,
  created_at timestamptz NOT NULL DEFAULT now()
);

DROP FUNCTION gold.search_books(text, int, boolean);

-- Every whitespace-separated term must appear as a substring (pg_bigm index on each LIKE).
CREATE FUNCTION gold.search_books(
  q text, lim int DEFAULT 20, korean_only boolean DEFAULT false, off int DEFAULT 0
)
RETURNS TABLE (isbn13 char(13), title text, authors text, publisher text, pub_year int, score real)
LANGUAGE plpgsql STABLE AS $$
DECLARE
  key   text := gold.search_key(q);
  terms text[] := array_remove(string_to_array(gold.search_key(q), ' '), '');
  cond  text := '';
  term  text;
BEGIN
  IF coalesce(cardinality(terms), 0) = 0 OR lim <= 0 THEN
    RETURN;
  END IF;
  FOREACH term IN ARRAY terms LOOP
    cond := cond || format(' AND d.search_text LIKE likequery(%L)', term);
  END LOOP;
  RETURN QUERY EXECUTE format(
    'SELECT d.isbn13, d.title, d.authors, d.publisher, d.pub_year,
            bigm_similarity(%L, gold.search_key(d.title))::real AS score
       FROM gold.search_doc d
      WHERE ($1 = false OR d.is_korean)
        AND NOT EXISTS (SELECT 1 FROM gold.takedown t WHERE t.isbn13 = d.isbn13) %s
      ORDER BY score DESC, d.pub_year DESC NULLS LAST, d.isbn13
      LIMIT $2 OFFSET $3', key, cond)
  USING korean_only, lim, greatest(off, 0);
END
$$;
