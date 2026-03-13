# Task 02: Add _flush_and_close_handle and refactor callers

## Background

Flush-and-close logic is duplicated in `_rotate_to_new_chunk` and `_close_handle_and_clear_state` in `sinks.py`. This task extracts that logic into a single private method and refactors both call sites. It depends on task 01 only for a clean baseline; no direct dependency on the constant change.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`:
  - Implement `_flush_and_close_handle(self) -> None`: if `self._gcs_write_handle` is not None, flush (if the handle has a `flush` attribute), close the handle, then set `self._gcs_write_handle = None`. Match the current 4-line block behaviour exactly.
  - Refactor `_rotate_to_new_chunk` to call `self._flush_and_close_handle()` then perform its own state updates (key, chunk, records count).
  - Refactor `_close_handle_and_clear_state` to call `self._flush_and_close_handle()` then perform its own state updates (key, timestamp).
- Add a concise Google-style docstring for `_flush_and_close_handle` (purpose, no Args/Returns).

**Acceptance criteria:** Both rotate and close paths use the new method; handle lifecycle behaviour is unchanged; no duplicated flush/close code.

## Testing Needed

- No new tests required; existing tests for chunk rotation and target close already cover this behaviour (black-box). Run full target-gcs test suite to confirm regression gate passes.
