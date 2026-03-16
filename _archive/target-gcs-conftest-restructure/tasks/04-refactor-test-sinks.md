# Task 04: Refactor test_sinks.py

## Background

Phase 3 of the plan refactors `loaders/target-gcs/tests/unit/test_sinks.py` to use conftest fixtures and test_helpers instead of local definitions. This task depends on Task 01 (test_helpers) and Task 02 (conftest).

## This Task

- **Refactor** `loaders/target-gcs/tests/unit/test_sinks.py`.
- Remove local definitions: `_patch_all_pattern_modules`, `build_sink`, `_key_from_open_call`, `FIXED_DATE`, and any local default config.
- Import `build_sink` from conftest; import `key_from_open_call` from test_helpers. Use `FIXED_DATE` or `fixed_date` from conftest.
- For tests that need a patched environment: request the `patch_all_pattern_modules` fixture (e.g. add it as a parameter to those test functions). Use the yielded mocks only where assertions already exist on call args or keys.
- Replace any ad hoc `with _patch_all_pattern_modules():` (or similar) with the fixture.
- **Preserve** all test names and assertion logic; no regressions. Use conftest fixtures and test_helpers throughout.

## Testing Needed

- Run `loaders/target-gcs/tests/unit/test_sinks.py` and the full target-gcs test suite. All tests must pass with unchanged assertions and test names. Black-box behaviour preserved; only the source of mocks, config, and helpers changes.
