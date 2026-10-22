CREATE EXTENSION IF NOT EXISTS pg_bigm;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE bronze.lod_dump (
  dump_id        serial PRIMARY KEY,
  dataset        text NOT NULL,              -- book|person|organization|subject
  format         text NOT NULL,
  file_name      text,
  file_sha256    text,
  dump_date      date,
  downloaded_at  timestamptz,
  resource_count int
);

CREATE TABLE bronze.lod_resource (
  resource_uri  text PRIMARY KEY,
  dataset       text NOT NULL,
  body          jsonb NOT NULL,              -- {predicate IRI: [values...]}
  body_sha256   bytea NOT NULL,
  first_dump_id int REFERENCES bronze.lod_dump (dump_id),
  last_dump_id  int REFERENCES bronze.lod_dump (dump_id),
  changed_at    timestamptz NOT NULL,
  deleted_at    timestamptz                  -- tombstone when missing from a later dump
);
CREATE INDEX lod_resource_changed_at ON bronze.lod_resource (changed_at);

CREATE TABLE bronze.api_payload (
  id             bigserial PRIMARY KEY,
  source         text NOT NULL,
  endpoint       text NOT NULL,
  request_params jsonb NOT NULL,             -- never contains the API key
  fetched_at     timestamptz NOT NULL,
  http_status    int,
  body           jsonb NOT NULL,
  body_sha256    bytea NOT NULL,
  UNIQUE (source, body_sha256)
);

CREATE TABLE bronze.source_record (
  source        text,
  source_key    text,
  isbn13        char(13),
  payload_id    bigint REFERENCES bronze.api_payload (id),
  record        jsonb NOT NULL,
  record_sha256 bytea NOT NULL,
  first_seen_at timestamptz,
  last_seen_at  timestamptz,
  changed_at    timestamptz NOT NULL,
  PRIMARY KEY (source, source_key)
);
CREATE INDEX source_record_changed_at ON bronze.source_record (changed_at);
CREATE INDEX source_record_isbn13 ON bronze.source_record (isbn13);
