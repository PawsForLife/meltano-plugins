# Task Plan: 04-add-write-record-as-jsonl

## Overview

This task deduplicates record serialization and write by introducing a single private method `_write_record_as_jsonl` on `GCSSink` and refactoring both record-processing paths to use it. Today, `_process_record_single_or_chunked` and `_process_record_hive_partitioned` each call `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default)` and write the result to the GCS write handle. Extracting this into one method preserves behaviour (payloads and newline endings unchanged) and removes duplication. Depends on tasks 01–03 (constant, `_flush_and_close_handle`, `_apply_key_prefix_and_normalize`) so that sinks.py refactors are applied in order.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Add `_write_record_as_jsonl(self, record: dict) -> None` that writes `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default)` to `self.gcs_write_handle`. Add Google-style docstring (purpose, Args for `record`, no Returns). Refactor `_process_record_single_or_chunked` to replace the inline `self.gcs_write_handle.write(orjson.dumps(...))` block with `self._write_record_as_jsonl(record)`. Refactor `_process_record_hive_partitioned` to replace the inline `self._gcs_write_handle.write(orjson.dumps(...))` block with `self._write_record_as_jsonl(record)` (call site may use property or private attribute; the new method writes via `self.gcs_write_handle` per interfaces). |

No new files. No changes to helpers, target.py, or tests (existing tests remain the regression gate).

## Test Strategy

1. **No new tests.** Existing tests for chunked and hive-partitioned record write already validate written content (black-box). Tests that assert on written payloads, line endings, or record content will continue to pass because behaviour is unchanged.
2. **Regression:** Run the full target-gcs test suite after refactor. Any test that feeds records and asserts on GCS output (e.g. written lines, file contents) is the oracle for correct behaviour.
3. **TDD:** Not required for this task; the change is a pure extract-method refactor with no new branches or edge cases.

## Implementation Order

1. **Implement `_write_record_as_jsonl`** in `sinks.py`:
   - Signature: `def _write_record_as_jsonl(self, record: dict) -> None`
   - Body: `self.gcs_write_handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default))`. Use existing `_json_default` from `.helpers` (already imported in sinks.py).
   - Add Google-style docstring: purpose (write a single record as JSONL to the current GCS write handle), Args (`record`: record dict to serialize and write), no Returns.
   - Place the method near other record-writing or handle-using logic (e.g. after `_close_handle_and_clear_state` / before or near `_process_record_single_or_chunked`).
2. **Refactor `_process_record_single_or_chunked`:**
   - Remove the block that does `self.gcs_write_handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default))`.
   - Replace with `self._write_record_as_jsonl(record)`.
3. **Refactor `_process_record_hive_partitioned`:**
   - Remove the block that does `self._gcs_write_handle.write(orjson.dumps(...))`.
   - Replace with `self._write_record_as_jsonl(record)`.
4. Run the full target-gcs test suite and fix any regressions.

## Validation Steps

1. From `loaders/target-gcs/`: run `uv run pytest`; all tests pass.
2. Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs`; no new issues.
3. Optionally run `uv run mypy target_gcs` if the project runs it.
4. Confirm that written payloads and line endings are unchanged (existing tests that assert on written content are the oracle).

## Documentation Updates

- **Code:** Docstring for `_write_record_as_jsonl` only. No README or external docs change for this task.
- **AI context:** No update required unless a later task (e.g. 09) refreshes component docs; this task does not change public behaviour or interfaces.
