# Task Plan: 02-add-flush-and-close-handle

## Overview

This task removes duplicated flush-and-close logic from `_rotate_to_new_chunk` and `_close_handle_and_clear_state` in `sinks.py` by introducing a single private method `_flush_and_close_handle(self) -> None`. Both callers delegate handle lifecycle to this method, then perform their own state updates. Behaviour is unchanged; existing tests remain the regression gate.

**Feature context:** Part of target-gcs-dedup-split-logic (unify repeated logic into shared sink-private methods). See [master implementation.md](../master/implementation.md) step 2.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Add `_flush_and_close_handle`; refactor `_rotate_to_new_chunk` and `_close_handle_and_clear_state` to call it. |

**No new files.** No changes to helpers, tests, or config.

### sinks.py — Specific changes

1. **Add `_flush_and_close_handle`** (place after `gcs_write_handle` property, before `_rotate_to_new_chunk`):
   - Signature: `def _flush_and_close_handle(self) -> None`
   - Body: if `self._gcs_write_handle is not None`: call `flush()` only when `hasattr(self._gcs_write_handle, "flush")`, then `close()`, then set `self._gcs_write_handle = None`. Match the current 4-line block exactly.
   - Docstring: Google-style; state purpose (flush and close current GCS write handle and set it to None; safe when handle has no `flush`). No Args/Returns.

2. **Refactor `_rotate_to_new_chunk`**:
   - Replace the 4-line flush/close block with `self._flush_and_close_handle()`.
   - Keep unchanged: `self._key_name = ""`, `self._chunk_index += 1`, `self._records_written_in_current_file = 0`, `self._current_timestamp = round((self._time_fn or time.time)())`.

3. **Refactor `_close_handle_and_clear_state`**:
   - Replace the 4-line flush/close block with `self._flush_and_close_handle()`.
   - Keep unchanged: `self._key_name = ""`, `self._current_timestamp = None`.

## Test Strategy

- **No new tests.** The task document and master testing plan state that existing tests for chunk rotation and target close already cover this behaviour (black-box). Regression is verified by running the full target-gcs test suite.
- **TDD:** Not applicable for this task—pure refactor with no new public surface; existing tests are the gate.

## Implementation Order

1. Add `_flush_and_close_handle` with the 4-line logic and docstring, placed immediately before `_rotate_to_new_chunk`.
2. In `_rotate_to_new_chunk`, remove the inline flush/close block and call `self._flush_and_close_handle()` at the start, then retain all existing state updates.
3. In `_close_handle_and_clear_state`, remove the inline flush/close block and call `self._flush_and_close_handle()` at the start, then retain all existing state updates.
4. Run the target-gcs test suite to confirm no regressions.

## Validation Steps

1. **Tests:** From `loaders/target-gcs/`, run `uv run pytest`. All tests must pass (no new xfail).
2. **Linting/formatting:** Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs` (or project equivalent). Resolve any issues in modified files.
3. **Type check:** Run `uv run mypy target_gcs` if the project uses mypy; no new errors in `sinks.py`.
4. **Smoke:** Confirm that tests that exercise chunk rotation (e.g. `max_records_per_file`) and sink close (e.g. target standard tests, hive partition change) still pass—they validate handle lifecycle without asserting on internals.

## Documentation Updates

- **Code:** The new method has a concise Google-style docstring only. No separate docs folder updates.
- **AI context / README:** No changes required for this task.
