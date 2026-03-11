# Task Plan: 03-sink-state-and-time-injection

**Feature:** target-gcs-file-chunking-by-record-count  
**Task:** Add per-stream chunking state and injectable time to GCSSink so rotation (later tasks) and key assertions in tests are deterministic.

---

## Overview

This task adds the per-stream state required for record-count-based chunking (`_records_written_in_current_file`, `_chunk_index`) and makes the time used for key generation injectable so tests can assert key content without flakiness. No rotation or key-format logic is implemented here; that is done in tasks 05 and 06. Existing behaviour and tests remain unchanged. Completion of task 01 (config schema) is assumed so that `max_records_per_file` exists in config; this task does not read it yet.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | In `GCSSink.__init__`: add `self._records_written_in_current_file: int = 0`, `self._chunk_index: int = 0`, and optional `time_fn` (keyword-only, default `None`). Store `time_fn` as `self._time_fn`. In `key_name` property: use `(self._time_fn or time.time)()` for `extraction_timestamp` so key generation is testable. Add brief comment that time is injectable for tests. |
| `loaders/target-gcs/tests/test_sinks.py` | If `time_fn` is added: add one test that builds a sink with a custom `time_fn` returning a fixed value and asserts `key_name` contains that timestamp (e.g. convention `file/{timestamp}.txt` and assert `subject.key_name == "file/12345.txt"`). If the decision is to use `time.time()` and document patching only: no new test in this task (tasks 04/05 will patch `time`). |

No new files. No changes to `target.py` (time_fn is sink-only for this task; target does not pass it in production).

---

## Test Strategy

**TDD:** Run existing tests first; they must still pass after adding state and time injection. Then, if implementing optional `time_fn`:

1. **Time injection (when time_fn is added):** Add a test that builds a sink with `time_fn` returning a fixed value (e.g. `lambda: 12345.0`) and a key convention that includes `{timestamp}`; assert `key_name` contains the fixed value (e.g. `"12345"` in the key). Purpose: ensure key generation uses the injectable time so later tests (rotation, chunk index in key) can be deterministic without patching. Docstring: WHAT (key_name uses injectable time when provided), WHY (deterministic key assertions in tests).
2. **Regression:** All existing tests in `test_sinks.py` continue to pass. No assertions on call counts or logs; assert only observable behaviour (key string, handle usage).

If the implementation choice is “no time_fn, patch `time` in tests”: no new test in this task; add a one-line comment in `sinks.py` in the key-computation block that time is patchable for tests. Tasks 04 and 05 will patch `gcs_target.sinks.time`.

---

## Implementation Order

1. **Run existing tests** from `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py` — establish baseline pass.
2. **Implement state and time in sinks.py:**
   - In `GCSSink.__init__`, after existing `_gcs_write_handle` and `_key_name` initialization, add:
     - `self._records_written_in_current_file: int = 0`
     - `self._chunk_index: int = 0`
   - Add optional keyword-only parameter to `__init__`: `time_fn: Optional[Callable[[], float]] = None`. Store as `self._time_fn = time_fn`. Ensure `__init__` signature remains compatible with SDK instantiation `GCSSink(target, stream_name, schema, key_properties)` (time_fn is keyword-only with default).
   - In `key_name` property: replace `extraction_timestamp = round(time.time())` with `extraction_timestamp = round((self._time_fn or time.time)())`. Add a short comment that time is injectable for tests.
   - Add `Optional` and `Callable` to typing imports if not present.
3. **If time_fn is added:** Add test in `test_sinks.py`: build sink with a custom `time_fn` (e.g. via a helper that accepts `time_fn` and passes it to `GCSSink`) and key_naming_convention including `{timestamp}`; assert the resulting `key_name` contains the fixed timestamp. Run tests until they pass.
4. **Run full test suite and lint** for target-gcs: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy gcs_target`.

---

## Validation Steps

- All existing tests in `test_sinks.py` pass (no regressions).
- If time_fn implemented: new test that injects `time_fn` and asserts key contains fixed timestamp passes.
- From `loaders/target-gcs/`: `uv run pytest` passes; `uv run ruff check .` and `uv run ruff format --check` pass; `uv run mypy gcs_target` passes.
- Acceptance: GCSSink has `_records_written_in_current_file` and `_chunk_index` initialized to 0; key generation uses injectable time when provided (or `time.time()` otherwise); no rotation or key-format logic yet.

---

## Documentation Updates

None required for this task. Optional: if `time_fn` is added, a brief note in `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` or in master plan testing.md that tests can pass `time_fn` for deterministic keys is acceptable but not mandatory; the main contract is in the code and task plan.
