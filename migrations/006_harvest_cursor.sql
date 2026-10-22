-- Progress of resumable full harvests: the last page committed to bronze.
CREATE TABLE bronze.harvest_cursor (
  name         text PRIMARY KEY,
  page_no      int NOT NULL,
  page_size    int NOT NULL,
  total_count  int,
  updated_at   timestamptz NOT NULL,
  completed_at timestamptz
);
