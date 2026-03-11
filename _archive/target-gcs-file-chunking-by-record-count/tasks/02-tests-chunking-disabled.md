# Background

When `max_records_per_file` is unset or 0, behaviour must match the current implementation: one key and one handle per stream, no rotation, no `chunk_index` in the key. These tests lock in backward compatibility and will fail until the sink initializes chunking state and skips rotation when the setting is 0 or absent (tasks 03 and 06).

**Depends on:** 01-add-config-schema (so config with/without the key is valid).

# This Task

- **File:** `loaders/target-gcs/tests/test_sinks.py`
- Add tests using the existing `build_sink(config=...)` pattern; patch `gcs_target.sinks.Client` and `smart_open.open` as in existing tests.
- **Test 1 — One key and one handle when chunking disabled:** Build sink with no `max_records_per_file` (or `max_records_per_file: 0`). Write multiple records (e.g. 5). Assert `key_name` is unchanged after multiple writes. Assert only one handle is opened (e.g. exactly one `smart_open.open` call, or one close over the run). Purpose: ensures no rotation when option is off.
- **Test 2 — Key has no chunk_index when convention omits it:** Build sink without chunking. Set a convention that does not use `{chunk_index}`. Assert `key_name` does not contain a literal `{chunk_index}` and matches the existing pattern (stream, date, timestamp only). Purpose: ensures key format is unchanged when chunking is disabled.
- Add clear docstrings to each test: WHAT is being tested and WHY (backward compatibility).

# Testing Needed

- Run the new tests; they may fail until task 03 (sink state) and task 06 (rotation logic that only runs when `max_records_per_file > 0`) are implemented. Once those are done, these tests must pass.
- Do not assert on "called_once" or log lines; assert on observable behaviour (key stability, number of opens/closes, key string content).
