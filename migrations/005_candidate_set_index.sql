CREATE INDEX candidate_set_isbn13 ON silver.candidate ((body ->> 'set_isbn13'))
  WHERE body ->> 'set_isbn13' IS NOT NULL;
