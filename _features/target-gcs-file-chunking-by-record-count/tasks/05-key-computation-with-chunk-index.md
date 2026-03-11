# Background

When chunking is enabled, the key must include `chunk_index` in the format map so conventions like `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl` produce distinct keys per chunk. When `_key_name` is cleared during rotation, the next access to `key_name` must recompute using current time and the new `_chunk_index`.

**Depends on:** 01-add-config-schema, 03-sink-state-and-time-injection.

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- In the `key_name` property:
  - When `_key_name` is non-empty, return it (unchanged).
  - When computing a new key (`_key_name` empty): obtain `max_records = self.config.get("max_records_per_file", 0)`.
  - Build the format map with `stream`, `date`, `timestamp` (using current time via `time.time()` or injected `time_fn`). If `max_records` is present and `max_records > 0`, add `chunk_index=self._chunk_index` to the format map so that `key_naming_convention` may use `{chunk_index}`.
  - When chunking is disabled, do not add `chunk_index` to the format map (existing behaviour).
- **Acceptance criteria:** With chunking off, key behaviour is unchanged. With chunking on, after rotation clears `_key_name`, the next `key_name` access returns a key that includes the updated `_chunk_index` and current timestamp. Existing tests and task 02 tests pass; task 04 tests that only need key format may pass after this; rotation tests still need task 06.

# Testing Needed

- Run full `test_sinks.py` including task 02 and 04 tests. Fix any failures caused by key computation (e.g. missing chunk_index when chunking on, or chunk_index present when chunking off). Task 04 "key format with chunk_index" test should pass once rotation (06) clears `_key_name` and increments `_chunk_index`.
