-- Read-optimized layer derived from silver.

CREATE FUNCTION gold.search_key(s text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
  SELECT btrim(regexp_replace(lower(normalize(coalesce(s, ''), NFKC)), '\s+', ' ', 'g'))
$$;

CREATE TABLE gold.search_doc (
  isbn13       char(13) PRIMARY KEY,
  title        text,
  authors      text,
  publisher    text,
  series_title text,
  kdc          text,
  add_reader   char(1),
  binding      text,
  pub_year     int,
  is_korean    boolean,
  search_text  text NOT NULL   -- search_key(title x2, remainder, authors, publisher, series, subjects)
);
CREATE INDEX search_doc_bigm ON gold.search_doc USING gin (search_text gin_bigm_ops);

-- Every whitespace-separated term must appear as a substring (pg_bigm index on each LIKE).
CREATE FUNCTION gold.search_books(q text, lim int DEFAULT 20, korean_only boolean DEFAULT false)
RETURNS TABLE (isbn13 char(13), title text, authors text, publisher text, pub_year int, score real)
LANGUAGE plpgsql STABLE AS $$
DECLARE
  key   text := gold.search_key(q);
  terms text[] := array_remove(string_to_array(gold.search_key(q), ' '), '');
  cond  text := '';
  term  text;
BEGIN
  IF coalesce(cardinality(terms), 0) = 0 THEN
    RETURN;
  END IF;
  FOREACH term IN ARRAY terms LOOP
    cond := cond || format(' AND d.search_text LIKE likequery(%L)', term);
  END LOOP;
  RETURN QUERY EXECUTE format(
    'SELECT d.isbn13, d.title, d.authors, d.publisher, d.pub_year,
            bigm_similarity(%L, gold.search_key(d.title))::real AS score
       FROM gold.search_doc d
      WHERE ($1 = false OR d.is_korean) %s
      ORDER BY score DESC, d.pub_year DESC NULLS LAST, d.isbn13
      LIMIT $2', key, cond)
  USING korean_only, lim;
END
$$;
