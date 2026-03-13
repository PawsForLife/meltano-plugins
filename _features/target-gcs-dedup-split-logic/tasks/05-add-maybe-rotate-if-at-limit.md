# Task 05: Add _maybe_rotate_if_at_limit and refactor record-processing methods

## Background

Both record-processing methods duplicate the "rotate if at max_records_per_file limit" block. This task extracts that into a single private method and refactors both to call it before writing. Depends on task 04 so that the same methods already use `_write_record_as_jsonl`; this task adds the rotate check before the write call.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`:
  - Implement `_maybe_rotate_if_at_limit(self) -> None`: read `max_records = self.config.get("max_records_per_file", 0)`; treat 0 or missing as no limit. If `max_records > 0` and `self._records_written_in_current_file >= max_records`, call `self._rotate_to_new_chunk()`.
  - Refactor `_process_record_single_or_chunked` to call `self._maybe_rotate_if_at_limit()` before `self._write_record_as_jsonl(record)`.
  - Refactor `_process_record_hive_partitioned` to call `self._maybe_rotate_if_at_limit()` before `self._write_record_as_jsonl(record)`.
- Add a Google-style docstring for `_maybe_rotate_if_at_limit` (purpose, no Args/Returns).

**Acceptance criteria:** Rotation at limit happens in one place; both record paths call the new method before writing; behaviour unchanged (same rotation timing and file counts).

## Testing Needed

- No new tests; existing tests for max_records_per_file and chunk rotation cover this behaviour. Run full target-gcs test suite to confirm regression gate passes.
