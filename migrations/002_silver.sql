-- Normalized, merged layer. Fully rebuildable from bronze.

CREATE TABLE silver.candidate (            -- one source's mapped view of one ISBN
  source     text NOT NULL,
  source_key text NOT NULL,
  isbn13     char(13) NOT NULL,
  body       jsonb NOT NULL,              -- CandidateRecord.to_json()
  PRIMARY KEY (source, source_key, isbn13)
);
CREATE INDEX candidate_isbn13 ON silver.candidate (isbn13);

CREATE TABLE silver.edition (
  isbn13               char(13) PRIMARY KEY,
  isbn10               char(10),
  primary_resource_uri text,
  title                text NOT NULL,
  remainder_of_title   text,
  title_normalized     text NOT NULL,
  title_hanja          text,
  volume_label         text,
  edition_statement    text,
  responsibility_stmt  text,
  publisher            text,
  publisher_normalized text,
  publication_place    text,
  pub_date             date,
  pub_date_precision   text CHECK (pub_date_precision IN ('day', 'month', 'year')),
  pub_status           text NOT NULL CHECK (pub_status IN ('announced', 'published')),
  extent_raw           text,
  page_count           int,
  height_cm            numeric(5, 1),
  width_mm             int,
  height_mm            int,
  volumes              int,
  binding              text CHECK (binding IN ('paper', 'ebook', 'audio', 'mixed', 'other')),
  form                 text,
  ea_add_code          char(5),
  add_reader           char(1),
  add_form             char(1),
  add_kdc_class        char(1),
  add_kdc_division     char(2),
  kdc                  text,
  kdc_edition          text,
  ddc                  text,
  nlk_call_no          text,
  language             text,
  original_title       text,
  series_title         text,
  series_no            text,
  price_planned        int,
  price_real           int,
  cover_url            text,                -- hotlink only
  deposit_yn           boolean,
  cip_control_no       text,
  related_isbn_raw     text,
  is_korean            boolean NOT NULL,
  provenance           jsonb NOT NULL,      -- {field: chosen source}
  content_hash         bytea NOT NULL,
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE silver.edition_record_link (
  isbn13     char(13) NOT NULL REFERENCES silver.edition ON DELETE CASCADE,
  source     text NOT NULL,
  source_key text NOT NULL,
  link_role  text NOT NULL CHECK (link_role IN ('primary', 'secondary', 'conflict')),
  PRIMARY KEY (source, source_key, isbn13)
);
CREATE INDEX edition_record_link_isbn13 ON silver.edition_record_link (isbn13);

CREATE TABLE silver.manifestation_no_isbn (
  resource_uri        text PRIMARY KEY,
  title               text,
  responsibility_stmt text,
  publisher           text,
  issued_year         int,
  kdc                 text
);

CREATE TABLE silver.edition_contributor (
  isbn13          char(13) NOT NULL REFERENCES silver.edition ON DELETE CASCADE,
  ordinal         int NOT NULL,
  name            text NOT NULL,
  name_normalized text NOT NULL,
  role            text NOT NULL,
  role_raw        text,
  source          text NOT NULL,
  PRIMARY KEY (isbn13, ordinal)
);

CREATE TABLE silver.book_set (
  set_isbn13     char(13) PRIMARY KEY,
  set_add_code   char(5),
  set_expression text,
  title          text,
  total_volumes  int,
  is_open_ended  boolean NOT NULL
);

CREATE TABLE silver.set_member (
  set_isbn13   char(13) NOT NULL REFERENCES silver.book_set ON DELETE CASCADE,
  isbn13       char(13) NOT NULL REFERENCES silver.edition ON DELETE CASCADE,
  volume_label text,
  PRIMARY KEY (set_isbn13, isbn13)
);

CREATE TABLE silver.edition_subject (
  isbn13 char(13) NOT NULL REFERENCES silver.edition ON DELETE CASCADE,
  scheme text NOT NULL
    CHECK (scheme IN ('kdc', 'ddc', 'add_code', 'ksh', 'nlk_keyword', 'seoji_subject')),
  code   text NOT NULL,
  label  text,
  source text NOT NULL,
  PRIMARY KEY (isbn13, scheme, code, source)
);

CREATE TABLE silver.edition_rich_text (     -- possibly third-party works: not redistributable
  isbn13          char(13) NOT NULL REFERENCES silver.edition ON DELETE CASCADE,
  kind            text NOT NULL CHECK (kind IN ('toc', 'introduction', 'summary', 'abstract')),
  source          text NOT NULL,
  body            text NOT NULL,
  redistributable boolean NOT NULL DEFAULT false,
  PRIMARY KEY (isbn13, kind, source)
);

CREATE TABLE silver.field_provenance (
  isbn13     char(13) NOT NULL REFERENCES silver.edition ON DELETE CASCADE,
  field      text NOT NULL,
  source     text NOT NULL,
  source_key text NOT NULL,
  raw_value  text,
  chosen     boolean NOT NULL,
  rule       text,
  PRIMARY KEY (isbn13, field, source, source_key)
);

CREATE TABLE silver.merge_issue (
  id          bigserial PRIMARY KEY,
  isbn13      char(13),
  kind        text NOT NULL
    CHECK (kind IN ('isbn_conflict', 'multi_lod', 'invalid_isbn', 'title_mismatch')),
  source      text,
  source_key  text,
  detail      jsonb NOT NULL DEFAULT '{}',
  created_at  timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);
CREATE INDEX merge_issue_isbn13 ON silver.merge_issue (isbn13);
CREATE INDEX merge_issue_source ON silver.merge_issue (source, source_key);

CREATE TABLE silver.build_state (
  id          serial PRIMARY KEY,
  kind        text NOT NULL,                -- rebuild|refresh
  started_at  timestamptz NOT NULL,
  finished_at timestamptz,
  editions    int
);
