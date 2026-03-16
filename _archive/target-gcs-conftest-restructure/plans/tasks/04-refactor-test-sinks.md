# Task Plan: 04-refactor-test-sinks

## Overview

This task refactors `loaders/target-gcs/tests/unit/test_sinks.py` to use shared conftest fixtures and test_helpers instead of local definitions. It implements **Phase 3 (refactor test_sinks)** of the master implementation plan. All test names and assertion logic are preserved; only the source of mocks, config, and helpers changes. **Prerequisites:** Task 01 (test_helpers with `key_from_open_call`) and Task 02 (conftest with `build_sink`, `patch_all_pattern_modules`, `FIXED_DATE`) must be complete.

**Scope:** Modify `test_sinks.py` only. No new files; no changes to production code or other test files.

---

## Files to Create / Modify

| Action | Path | Description |
|--------|------|-------------|
| **Modify** | `loaders/target-gcs/tests/unit/test_sinks.py` | Remove local definitions; add imports from conftest and test_helpers; request `patch_all_pattern_modules` fixture where tests need a patched environment; replace `_key_from_open_call(mock_open.call_args)` with `key_from_open_call(mock_open.call_args[0])`. |

**No new files.** No other files are modified.

---

## Test Strategy

- **No new tests.** This task is a refactor; existing tests in `test_sinks.py` are the regression gate.
- **TDD:** Not applicable; behaviour is unchanged. Run the test file and full target-gcs suite before and after refactor; all tests must pass with identical assertions and outcomes.
- **Black-box preserved:** Assertions remain on keys, key names, written payloads, exceptions, and observable mock behaviour (e.g. call_count, call_args) only where such assertions already exist. Do not add assertions on "called_once" or log output beyond what is already there.
- **Validation:** Run `pytest loaders/target-gcs/tests/unit/test_sinks.py -v` and then the full target-gcs suite (e.g. `pytest loaders/target-gcs/tests/ -v`). Every test must pass; no assertion changes; no new failures.

---

## Implementation Order

1. **Add imports (top of file)**  
   - Import `build_sink` from conftest (e.g. `from ...conftest import build_sink, FIXED_DATE` or equivalent relative import from `unit/` so that `loaders/target-gcs/tests/unit/test_sinks.py` imports from `loaders/target-gcs/tests/conftest.py`).  
   - Import `key_from_open_call` from test_helpers (e.g. `from ...test_helpers import key_from_open_call`).  
   - Keep existing imports: `re`, `Callable`, `datetime`, `Decimal`, `MagicMock`, `patch`, `orjson`, `pytest`, `GCSSink`, `GCSTarget`.  
   - Remove: `contextmanager` if no longer used after removing `_patch_all_pattern_modules`.

2. **Remove local definitions**  
   - Delete the `_patch_all_pattern_modules` context manager (entire function).  
   - Delete the local `build_sink` function.  
   - Delete the local `_key_from_open_call` function.  
   - Delete the module-level `FIXED_DATE = datetime(2024, 3, 11)`.

3. **Replace patch context with fixture**  
   - For every test that currently uses `with _patch_all_pattern_modules():` or `with _patch_all_pattern_modules(open_mock=..., client_mock=...):`, add `patch_all_pattern_modules` as a parameter to that test function. The fixture yields `(open_mock, client_mock)`.  
   - In the test body, unpack the fixture: e.g. `open_mock, client_mock = patch_all_pattern_modules` at the start of the test (or use the names in the parameter and assign: `mock_open, _ = patch_all_pattern_modules` if the test uses `mock_open` for the open mock).  
   - For tests that passed custom mocks (e.g. `_patch_all_pattern_modules(open_mock=mock_handle)`): request the fixture, then configure the yielded open_mock (e.g. `open_mock.return_value = mock_handle` or `open_mock.side_effect = mock_handles`) before building the sink and calling the code under test. Preserve existing assertions on call_count, call_args, or written payloads.  
   - Remove all `with _patch_all_pattern_modules(...):` blocks; the fixture is active for the whole test by virtue of being requested.

4. **Replace _key_from_open_call with key_from_open_call**  
   - The helper in test_helpers expects the **positional-args tuple** (i.e. `mock_open.call_args[0]`), not the full `call_args`.  
   - Replace every `_key_from_open_call(mock_open.call_args)` with `key_from_open_call(mock_open.call_args[0])`.  
   - Replace every `_key_from_open_call(c)` in a list comprehension (e.g. over `mock_open.call_args_list`) with `key_from_open_call(c[0])`.

5. **Use FIXED_DATE from conftest**  
   - Where tests use the literal `datetime(2024, 3, 11)` or the removed local `FIXED_DATE`, use the imported `FIXED_DATE` from conftest (or a local `fixed_date = datetime(2024, 3, 11)` only if the test intentionally uses a different value; otherwise use `FIXED_DATE`).  
   - Tests that already define a local `fixed_date` for a closure (e.g. `date_fn=lambda: fixed_date`) can keep that variable and set it to `FIXED_DATE` from conftest, or use `FIXED_DATE` directly in the lambda (e.g. `date_fn=lambda: FIXED_DATE`).

6. **Run tests and fix any regressions**  
   - Run `pytest loaders/target-gcs/tests/unit/test_sinks.py -v`. Fix any import errors, fixture name mismatches, or assertion failures so that all tests pass with unchanged behaviour.  
   - Run the full target-gcs test suite and confirm no regressions.

7. **Lint/format**  
   - Run the project linter/formatter on `test_sinks.py`; fix any issues.

---

## Validation Steps

- [ ] No local definitions remain: `_patch_all_pattern_modules`, `build_sink`, `_key_from_open_call`, and module-level `FIXED_DATE` are removed.
- [ ] Imports: `build_sink` and `FIXED_DATE` (where used) come from conftest; `key_from_open_call` comes from test_helpers.
- [ ] Every test that needed a patched environment requests the `patch_all_pattern_modules` fixture and uses the yielded `(open_mock, client_mock)`; tests that needed custom open behaviour configure the yielded open_mock (e.g. `return_value`, `side_effect`) before exercising the sink.
- [ ] All key assertions that used `_key_from_open_call(...)` now use `key_from_open_call(mock_open.call_args[0])` or `key_from_open_call(c[0])` for call_args_list.
- [ ] `pytest loaders/target-gcs/tests/unit/test_sinks.py -v` passes with the same number of tests and no failure.
- [ ] Full target-gcs suite passes: e.g. `pytest loaders/target-gcs/tests/ -v`.
- [ ] Project lint/format checks pass for `test_sinks.py`.

---

## Documentation Updates

- **None required.** No user-facing or AI context docs need to change for this task. Optional: if the test file had any inline comments that referred to "local helper" or "patch context", update them to mention "conftest fixture" or "test_helpers" where it improves clarity.

---

## Notes

- **Fixture usage:** Tests that do not need a patched environment (e.g. config/schema-only tests like `test_config_schema_excludes_key_naming_convention`, `test_sink_accepts_date_fn_and_stores_it`) do not request `patch_all_pattern_modules`; they only use `build_sink` (and optionally `FIXED_DATE`) from conftest.
- **Call signature for key_from_open_call:** test_helpers defines `key_from_open_call(call_args: tuple)` where `call_args` is the positional-args tuple (e.g. `mock.call_args[0]`). Passing `mock_open.call_args[0]` ensures the same key-extraction behaviour as the former local `_key_from_open_call(mock_open.call_args)` which used `call_args[0][0]` (first positional arg).
