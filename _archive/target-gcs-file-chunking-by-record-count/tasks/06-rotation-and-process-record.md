# Background

When `max_records_per_file > 0` and `_records_written_in_current_file >= max_records_per_file`, the sink must rotate before writing the next record: close and release the current handle, clear the key cache, increment chunk index, reset record count. Then write the record and increment the count. The record that would have exceeded the limit is written to the new file.

**Depends on:** 03-sink-state-and-time-injection, 05-key-computation-with-chunk-index.

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- In `process_record(self, record: dict, context: dict) -> None`:
  1. **Before writing:** If `max_records_per_file > 0` and `_records_written_in_current_file >= max_records_per_file`, run rotation:
     - If `_gcs_write_handle` is not None: flush the handle if it supports it (task 07), then close it; set `_gcs_write_handle = None`.
     - Set `_key_name = ""`.
     - Increment `_chunk_index`.
     - Set `_records_written_in_current_file = 0`.
  2. Write the record to `gcs_write_handle` (same as today: `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE)`).
  3. **After writing:** If `max_records_per_file > 0`, increment `_records_written_in_current_file`.
- Optional: extract a small helper `_rotate_to_new_chunk(self) -> None` that performs close, clear key, increment chunk index, reset count; keeps `process_record` readable.
- **Acceptance criteria:** Task 02 (chunking disabled) and task 04 (rotation at threshold, key format, record integrity) tests pass. No change to Singer RECORD handling or schema.

# Testing Needed

- Run all tests in `test_sinks.py`. Task 02 and 04 tests must pass. Existing tests must still pass (config without `max_records_per_file` implies no rotation).
- Regression: existing tests that do not set `max_records_per_file` must behave as before (one file per stream).
