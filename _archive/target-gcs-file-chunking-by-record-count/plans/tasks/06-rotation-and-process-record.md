# Task Plan: 06 — Rotation and process_record

**Feature:** target-gcs-file-chunking-by-record-count  
**Task file:** `tasks/06-rotation-and-process-record.md`  
**Depends on:** 03-sink-state-and-time-injection, 05-key-computation-with-chunk-index

---

## 1. Overview

This task implements record-count-based rotation and counter updates inside `GCSSink.process_record` in `loaders/target-gcs/gcs_target/sinks.py`. When `max_records_per_file > 0` and the current file has reached that many records, the sink rotates before writing the next record: close and release the current handle, clear the key cache, increment chunk index, reset the record counter, then write the record and increment the counter. The record that would have exceeded the limit is written to the new file. No change to Singer RECORD handling or schema.

**Scope:**

- **Before write:** If chunking is enabled and `_records_written_in_current_file >= max_records_per_file`, run rotation (close handle, clear `_key_name`, increment `_chunk_index`, set `_records_written_in_current_file = 0`). Flush before close when the handle supports it (task 07 refines flush behaviour; here call `flush()` before `close()` if the handle has it).
- **Write:** Unchanged: write record via `gcs_write_handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE))`.
- **After write:** If chunking is enabled, increment `_records_written_in_current_file`.
- **Optional:** Extract a helper `_rotate_to_new_chunk(self) -> None` to keep `process_record` readable.

**Acceptance:** Task 02 (chunking disabled) and task 04 (rotation at threshold, key format, record integrity) tests pass; existing tests without `max_records_per_file` still pass.

---

## 2. Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | Modify. Implement rotation check and execution at the start of `process_record`; optional `_rotate_to_new_chunk` helper; counter increment after write when chunking enabled. |

**Specific changes in `sinks.py`:**

- **In `process_record`:**
  1. **Before writing:**  
     - Read `max_records = self.config.get("max_records_per_file", 0)`.  
     - If `max_records > 0` and `self._records_written_in_current_file >= max_records`:  
       - If `self._gcs_write_handle` is not None: call `flush()` on the handle if it has that method (e.g. `getattr(self._gcs_write_handle, "flush", lambda: None)()`), then `close()`; set `self._gcs_write_handle = None`.  
       - Set `self._key_name = ""`.  
       - Increment `self._chunk_index`.  
       - Set `self._records_written_in_current_file = 0`.  
  2. **Write:**  
     - Same as today: `self.gcs_write_handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE))`.  
  3. **After writing:**  
     - If `max_records > 0`, increment `self._records_written_in_current_file`.
- **Optional refactor:** Extract the rotation block into `def _rotate_to_new_chunk(self) -> None` that performs: close handle (with flush if supported), clear `_key_name`, increment `_chunk_index`, set `_records_written_in_current_file = 0`. Then in `process_record`, call `self._rotate_to_new_chunk()` when the condition holds.

**No new files.** No changes to `target.py`, tests, or docs in this task.

---

## 3. Test Strategy

- **No new tests in this task.** Task 02 and task 04 tests define the behaviour; this task implements it.
- **Run existing tests:** Execute the target-gcs test suite from `loaders/target-gcs/` (e.g. `uv run pytest`). Focus on:
  - **Task 02 tests:** Chunking disabled (no rotation, one file per stream) still pass.
  - **Task 04 tests:** `test_chunking_rotation_at_threshold`, `test_chunking_key_format_includes_chunk_index`, `test_chunking_record_integrity_no_duplicate_or_dropped` pass.
  - **Regression:** All other tests in `test_sinks.py` (and `test_core.py` if present) still pass; configs without `max_records_per_file` behave as before (one file per stream).

**TDD:** Tests were added in tasks 02 and 04; implementation in this task makes them pass. If any test fails, fix the implementation (or the test only if the test is wrong per project rules).

---

## 4. Implementation Order

1. **Implement rotation block (before write)**  
   - In `process_record`, at the top: get `max_records = self.config.get("max_records_per_file", 0)`.  
   - If `max_records > 0` and `self._records_written_in_current_file >= max_records`:  
     - Close current handle: if `self._gcs_write_handle` is not None, call flush (if supported), then `close()`, set `self._gcs_write_handle = None`.  
     - Clear key: `self._key_name = ""`.  
     - Increment chunk: `self._chunk_index += 1`.  
     - Reset counter: `self._records_written_in_current_file = 0`.

2. **Keep existing write**  
   - Leave the existing line that writes the record to `gcs_write_handle` unchanged.

3. **Add counter increment (after write)**  
   - After the write, if `max_records > 0`, increment `self._records_written_in_current_file`.

4. **(Optional) Extract `_rotate_to_new_chunk`**  
   - Move the rotation logic into `def _rotate_to_new_chunk(self) -> None` and call it from `process_record` when the condition holds. Ensures single responsibility and readability.

5. **Run tests**  
   - From `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py -v`. Fix any failing tests (implementation or, if applicable, test logic) until all pass.

---

## 5. Validation Steps

1. **Lint and type-check**  
   - From `loaders/target-gcs/`: `uv run ruff check gcs_target/`, `uv run ruff format --check gcs_target/`, `uv run mypy gcs_target/`. Resolve any new issues.

2. **Full test suite**  
   - From `loaders/target-gcs/`: `uv run pytest`. All tests pass (no unexpected failures).

3. **Chunking disabled**  
   - Task 02 tests: config without `max_records_per_file` (or `max_records_per_file: 0`) → one key, one handle per stream; no rotation.

4. **Chunking enabled**  
   - Task 04 tests: rotation at threshold (e.g. 2 records → two keys, two opens; third record in new file); key format includes chunk index when convention has `{chunk_index}`; record integrity (e.g. 25 records → 25 writes, no duplicate or dropped).

5. **Regression**  
   - Existing tests that do not set `max_records_per_file` continue to pass with unchanged behaviour.

---

## 6. Documentation Updates

- **No documentation changes in this task.** README and sample config are updated in task 08. Interfaces and behaviour are already described in the master plan (`interfaces.md`, `implementation.md`). If code comments are added (e.g. for `_rotate_to_new_chunk`), keep them concise (Google-style docstring if a helper is extracted).
