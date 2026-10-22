-- A dump is staged in full before it touches bronze.lod_resource, so subjects whose triples
-- are split across the file are merged first and compared against the pre-dump state.
CREATE UNLOGGED TABLE bronze.lod_stage (
  dump_id      int NOT NULL REFERENCES bronze.lod_dump (dump_id) ON DELETE CASCADE,
  resource_uri text NOT NULL,
  body         jsonb NOT NULL,
  body_sha256  bytea NOT NULL,
  PRIMARY KEY (dump_id, resource_uri)
);
