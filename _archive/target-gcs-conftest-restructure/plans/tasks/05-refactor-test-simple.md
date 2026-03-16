# Task Plan: 05-refactor-test-simple

## Overview

This task refactors `loaders/target-gcs/tests/unit/paths/test_simple.py` to use shared `build_simple_path` from conftest and `key_from_open_call` from test_helpers, removing local `_build_simple_path` and `_key_from_open_call`. It implements **Phase 4 (refactor path tests)** of the master implementation plan for the simple path module. All test names and assertion logic are preserved; only the source of the path builder and key helper changes. **Prerequisites:** Task 01 (test_helpers with `key_from_open_call`) and Task 02 (conftest with `build_simple_path`) must be complete.

**Scope:** Modify `test_simple.py` only. No new files; no changes to production code or other test files. Patch strategy: keep a local `patch("target_gcs.paths.simple.smart_open.open", ...)` per test (no conftest fixture change in this task).

---

## Files to Create / Modify

| Action | Path | Description |
|--------|------|-------------|
| **Modify** | `loaders/target-gcs/tests/unit/paths/test_simple.py` | Remove local `_build_simple_path` and `_key_from_open_call`; add imports for `build_simple_path` from conftest and `key_from_open_call` from test_helpers; replace all usages; keep existing per-test `patch("target_gcs.paths.simple.smart_open.open", ...)`. Preserve all test names and assertions. |

**No new files.** No other files are modified.

---

## Test Strategy

- **No new tests.** This task is a refactor; existing tests in `test_simple.py` are the regression gate.
- **TDD:** Not applicable; behaviour is unchanged. Run the test file and full target-gcs suite before and after refactor; all tests must pass with identical assertions and outcomes.
- **Test file path (unchanged):** `loaders/target-gcs/tests/unit/paths/test_simple.py` — one test file per source module (`target_gcs.paths.simple`); path under `tests/unit/paths/` mirrors source.
- **Black-box preserved:** Assertions remain on keys passed to open, record count per file (via keys), close behaviour, and `current_key`; no new assertions on call counts or log output beyond what already exists.

---

## Implementation Order

1. **Add imports (top of file)**  
   - Import `build_simple_path` from conftest: `from ...conftest import build_simple_path` (from `unit/paths/`, `...` resolves to `tests/`).  
   - Import `key_from_open_call` from test_helpers: `from ...test_helpers import key_from_open_call`.  
   - Retain existing imports: `datetime`, `typing.Any`, `unittest.mock.MagicMock`, `unittest.mock.patch`, `target_gcs.paths.simple.SimplePath`.

2. **Remove local definitions**  
   - Delete the entire `_build_simple_path` function.  
   - Delete the entire `_key_from_open_call` function.

3. **Replace builder and helper usages**  
   - Replace every call to `_build_simple_path(...)` with `build_simple_path(...)` using the same arguments (config, time_fn, date_fn, storage_client, extraction_date). Conftest’s `build_simple_path` merges config with `SAMPLE_CONFIG` and uses the same defaults (e.g. stream name) as the former local builder; if a test passed custom config (e.g. `date_format="%Y"`, `max_records_per_file`), pass it the same way.  
   - Replace every `_key_from_open_call(mock_open.call_args)` with `key_from_open_call(mock_open.call_args[0])` (test_helpers expects the positional-args tuple).  
   - Replace every `_key_from_open_call(c)` in a list over `mock_open.call_args_list` with `key_from_open_call(c[0])`.

4. **Keep local patch per test**  
   - Leave each test’s `with patch("target_gcs.paths.simple.smart_open.open", return_value=... or side_effect=...):` as-is. Do not add a conftest fixture (e.g. `patched_simple_open`) in this task; optional follow-up could introduce one to reduce repetition.

5. **Run tests and fix regressions**  
   - Run `pytest loaders/target-gcs/tests/unit/paths/test_simple.py -v`. Fix any import errors or assertion failures so that all tests pass with unchanged behaviour.  
   - Run the full target-gcs test suite and confirm no regressions.

6. **Lint/format**  
   - Run the project linter/formatter on `test_simple.py`; fix any issues.

---

## Validation Steps

- [ ] No local definitions remain: `_build_simple_path` and `_key_from_open_call` are removed.
- [ ] Imports: `build_simple_path` from conftest; `key_from_open_call` from test_helpers.
- [ ] All calls to the builder use `build_simple_path(...)` with equivalent arguments; all key extraction uses `key_from_open_call(mock_open.call_args[0])` or `key_from_open_call(c[0])` for call_args_list.
- [ ] Each test that opens a handle still uses a local `patch("target_gcs.paths.simple.smart_open.open", ...)`; test names and assertions are unchanged.
- [ ] `pytest loaders/target-gcs/tests/unit/paths/test_simple.py -v` passes with the same number of tests and no failure.
- [ ] Full target-gcs suite passes: e.g. `pytest loaders/target-gcs/tests/ -v`.
- [ ] Project lint/format checks pass for `test_simple.py`.

---

## Documentation Updates

- **None required.** No user-facing or AI context docs need to change for this task. Optional: if the test file has inline comments that refer to “local helper” or “local builder”, update them to mention “conftest” or “test_helpers” where it improves clarity.

---

## Notes

- **Optional fixture later:** If desired, a future task can add a conftest fixture (e.g. `patched_simple_open`) that patches `target_gcs.paths.simple.smart_open.open` and yields the mock, then refactor these tests to request it; this task keeps the existing per-test patch to minimise scope and avoid conftest changes.
- **Call signature for key_from_open_call:** test_helpers defines `key_from_open_call(call_args: tuple)` where `call_args` is the positional-args tuple (e.g. `mock.call_args[0]`). Use `key_from_open_call(mock_open.call_args[0])` and `key_from_open_call(c[0])` for items in `call_args_list`.
