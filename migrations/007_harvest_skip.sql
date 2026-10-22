-- Records the Seoji API cannot return even one at a time (e.g. resultCode 105), by offset.
CREATE TABLE bronze.harvest_skip (
  name          text NOT NULL,
  record_offset int NOT NULL,
  error_code    text,
  message       text,
  skipped_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (name, record_offset)
);
