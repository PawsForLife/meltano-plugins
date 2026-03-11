# Task Plan: 05 — Key Computation with Chunk Index

**Feature:** target-gcs-file-chunking-by-record-count
**Task file:** `tasks/05-key-computation-with-chunk-index.md`
**Depends on:** 01-add-config-schema, 03-sink-state-and-time-injection

---

## 1. Overview

This task extends the `key_name` property on `GCSSink` so that when a new key is computed (i.e. when `_key_name` is empty), the format map includes `chunk_index` when chunking is enabled (`max_records_per_file` present and > 0). When chunking is disabled, the format map is unchanged and no `chunk_index` is added, preserving existing key behaviour. Time for the key's `timestamp` is taken from the injectable time source added in task 03 (`_time_fn` or `time.time()`). This enables conventions like `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl` to produce distinct keys per chunk after rotation (task 06 clears `_key_name` and increments `_chunk_index`). No rotation logic is implemented in this task.

---

## 2. Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | Modify the `key_name` property only. When `_key_name` is non-empty, return it unchanged. When computing a new key: read `max_records = self.config.get("max_records_per_file", 0)`; build the format map with `stream`, `date`, and `timestamp` (using `(self._time_fn or time.time)()` for the timestamp). If `max_records` is present and `max_records > 0`, add `chunk_index=self._chunk_index` to the format map before calling `format_map`. When chunking is disabled, do not add `chunk_index` (existing behaviour). |

No new files. No changes to `target.py` or tests in this task; existing and task-02/04 tests are used for validation.

---

## 3. Test Strategy

- **No new tests in this task.** Task 04 already defines tests for rotation and key format (including key format with `chunk_index`). Task 05 only implements key computation; rotation is implemented in task 06.
- **Run existing tests:** Execute the full `test_sinks.py` suite from `loaders/target-gcs/`. After this task:
  - Chunking-disabled behaviour must be unchanged (task 02 tests and any tests that do not set `max_records_per_file` continue to pass).
  - With chunking enabled, the **first** computed key must include `chunk_index` when the convention uses `{chunk_index}` (e.g. a test that builds a sink with chunking on and a convention containing `{chunk_index}`, then reads `key_name` once, can assert the key contains the chunk index value 0). Task 04's "key format with chunk_index" test may still fail until task 06 implements rotation (second key with chunk_index 1); fix only those failures that are clearly due to key computation (e.g. missing `chunk_index` in format map when chunking on, or `chunk_index` present when chunking off).
- **Black-box:** Assertions remain on observable behaviour (key string content, handle usage). No assertions on call counts or logs.

---

## 4. Implementation Order

1. **Open `loaders/target-gcs/gcs_target/sinks.py`** and locate the `key_name` property. Ensure task 03 is applied (presence of `_chunk_index`, `_time_fn`, and use of injectable time for the key timestamp).
2. **When `_key_name` is empty (compute path):**
   - Obtain `max_records = self.config.get("max_records_per_file", 0)`.
   - Compute `extraction_timestamp` using `(self._time_fn or time.time)()` (already in place if task 03 is done).
   - Build the `defaultdict(str, ...)` format map with `stream`, `date`, and `timestamp` as before.
   - If `max_records` is present and `max_records > 0`, add `chunk_index=self._chunk_index` to the format map.
   - Use this format map in the existing `prefixed_key_name.format_map(...)` call; do not add `chunk_index` when chunking is disabled.
3. **Leave the "if not self._key_name" branch structure intact:** when `_key_name` is non-empty, return it without recomputing (unchanged).
4. **Run tests:** From `loaders/target-gcs/`, run `uv run pytest tests/test_sinks.py -v`. Fix any regressions caused by key computation (e.g. KeyError if a convention uses `{chunk_index}` but it was not in the map when chunking off — conventions that do not use `{chunk_index}` must still work without it in the map because `defaultdict(str)` supplies an empty string for missing keys; ensure chunking-off path does not add `chunk_index` so behaviour is unchanged).
5. **Run lint and type check:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy gcs_target`.

---

## 5. Validation Steps

- From `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py` — all tests that do not depend on rotation (task 06) pass. Task 02 (chunking disabled) tests pass. No regression in existing sink tests.
- With chunking enabled and a key convention that includes `{chunk_index}`, the first access to `key_name` (before any rotation) returns a key containing the chunk index value `0`.
- With chunking disabled (or `max_records_per_file` 0/absent), key format is unchanged and no `chunk_index` is added to the format map; conventions that do not use `{chunk_index}` continue to work.
- Ruff and mypy pass with no new issues.

---

## 6. Documentation Updates

None required for this task. The key contract is described in the master plan interfaces.md (GCSSink.key_name with chunk_index in format map when chunking enabled). README and sample config are updated in task 08.
