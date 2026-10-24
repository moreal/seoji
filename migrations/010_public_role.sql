-- Least-privilege role for the public server (seoji serve): SELECT on exactly the tables the
-- query layer reads. silver.edition_rich_text (책소개·목차·서평) is deliberately not granted;
-- enabling it needs SEOJI_PUBLIC_RICH_TEXT=true AND
--   GRANT SELECT ON silver.edition_rich_text TO seoji_public;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'seoji_public') THEN
    CREATE ROLE seoji_public NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
END
$$;
ALTER ROLE seoji_public SET default_transaction_read_only = on;
ALTER ROLE seoji_public SET statement_timeout = '3s';

GRANT USAGE ON SCHEMA gold, silver TO seoji_public;
GRANT SELECT ON gold.search_doc, gold.takedown TO seoji_public;
GRANT SELECT ON silver.edition, silver.edition_contributor, silver.edition_subject,
                silver.set_member, silver.book_set, silver.build_state TO seoji_public;
GRANT EXECUTE ON FUNCTION gold.search_books(text, int, boolean, int, int),
                          gold.search_key(text) TO seoji_public;
