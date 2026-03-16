# Task 05: Refactor test_simple.py (paths)

## Background

Phase 4 of the plan refactors path tests to use conftest path builders and test_helpers. This task covers `loaders/target-gcs/tests/unit/paths/test_simple.py`. Depends on Task 01 (test_helpers) and Task 02 (conftest).

## This Task

- **Refactor** `loaders/target-gcs/tests/unit/paths/test_simple.py`.
- Remove local `_build_simple_path` and `_key_from_open_call`. Import `build_simple_path` from conftest and `key_from_open_call` from test_helpers (relative imports as appropriate for `unit/paths/`).
- Either keep a local patch of `target_gcs.paths.simple.smart_open.open` per test or add a conftest fixture (e.g. `patched_simple_open`) that patches that module and yields the mock; refactor tests to use the fixture where it reduces duplication.
- **Preserve** all assertions and test names; no regressions. Use conftest fixtures and test_helpers only.

## Testing Needed

- Run `loaders/target-gcs/tests/unit/paths/test_simple.py` and the full target-gcs test suite. All tests must pass with unchanged assertions and test names. Black-box behaviour preserved.
