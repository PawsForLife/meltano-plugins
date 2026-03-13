# Task Plan: 05-add-maybe-rotate-if-at-limit

## Overview

This task removes the duplicated "rotate if at max_records_per_file limit" block from `_process_record_single_or_chunked` and `_process_record_hive_partitioned` in `sinks.py` by introducing a single private method `_maybe_rotate_if_at_limit(self) -> None`. Both record-processing methods call it immediately before writing the record (before `_write_record_as_jsonl(record)` once task 04 is applied, or before the existing inline write when implementing in isolation). Rotation timing and file counts remain unchanged; existing tests are the regression gate.

**Feature context:** Part of target-gcs-dedup-split-logic (unify repeated logic into shared sink-private methods). See [master implementation.md](../master/implementation.md) step 5.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Add `_maybe_rotate_if_at_limit`; refactor both record-processing methods to call it before writing. |

**No new files.** No changes to helpers, tests, or config.

### sinks.py — Specific changes

1. **Add `_maybe_rotate_if_at_limit`** (place after `_close_handle_and_clear_state`, before `_process_record_single_or_chunked`):
   - Signature: `def _maybe_rotate_if_at_limit(self) -> None`
   - Body: `max_records = self.config.get("max_records_per_file", 0)`. Treat 0 or missing as no limit. If `max_records > 0` and `self._records_written_in_current_file >= max_records`, call `self._rotate_to_new_chunk()`.
   - Docstring: Google-style; state purpose (rotate to a new chunk when max_records_per_file is set and the current file has reached that limit). No Args/Returns.

2. **Refactor `_process_record_single_or_chunked`**:
   - Remove the 5-line block that reads `max_records`, checks `max_records and max_records > 0` and `_records_written_in_current_file >= max_records`, and calls `_rotate_to_new_chunk()`.
   - Insert `self._maybe_rotate_if_at_limit()` immediately before the write (i.e. before `self._write_record_as_jsonl(record)` if task 04 is done, or before the existing `self.gcs_write_handle.write(...)` otherwise).
   - Leave the write and the `_records_written_in_current_file += 1` logic unchanged.

3. **Refactor `_process_record_hive_partitioned`**:
   - Remove the 5-line block that reads `max_records`, checks the same condition, and calls `_rotate_to_new_chunk()`.
   - Insert `self._maybe_rotate_if_at_limit()` immediately before the write (same placement as above).
   - Leave partition/key handling, open-handle logic, write, and record-count increment unchanged.

## Test Strategy

- **No new tests.** The task document and master testing plan state that existing tests for `max_records_per_file` and chunk rotation cover this behaviour (black-box). Regression is verified by running the full target-gcs test suite.
- **TDD:** Not applicable—pure refactor with no new public surface; existing tests are the gate.

## Implementation Order

1. Add `_maybe_rotate_if_at_limit` with the logic and docstring, placed immediately before `_process_record_single_or_chunked`.
2. In `_process_record_single_or_chunked`, remove the inline rotate-if-at-limit block and call `self._maybe_rotate_if_at_limit()` once, immediately before the write.
3. In `_process_record_hive_partitioned`, remove the inline rotate-if-at-limit block and call `self._maybe_rotate_if_at_limit()` once, immediately before the write.
4. Run the target-gcs test suite to confirm no regressions.

## Validation Steps

1. **Tests:** From `loaders/target-gcs/`, run `uv run pytest`. All tests must pass (no new xfail).
2. **Linting/formatting:** Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs`. Resolve any issues in modified files.
3. **Type check:** Run `uv run mypy target_gcs`; no new errors in `sinks.py`.
4. **Smoke:** Confirm tests that exercise `max_records_per_file` and chunk rotation (e.g. multiple files when limit is reached) still pass—they validate rotation timing and file counts without asserting on internals.

## Documentation Updates

- **Code:** The new method has a concise Google-style docstring only. No separate docs folder updates.
- **AI context / README:** No changes required for this task.
