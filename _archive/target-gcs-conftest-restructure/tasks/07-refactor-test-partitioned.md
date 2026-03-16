# Task 07: Refactor test_partitioned.py (paths)

## Background

Phase 4 of the plan refactors path tests to use conftest path builders and test_helpers. This task covers `loaders/target-gcs/tests/unit/paths/test_partitioned.py`. Depends on Task 01 (test_helpers) and Task 02 (conftest).

## This Task

- **Refactor** `loaders/target-gcs/tests/unit/paths/test_partitioned.py`.
- Remove local path builder and `_key_from_open_call`. Import `build_partitioned_path` and `key_from_open_call` from conftest/test_helpers (relative imports as appropriate for `unit/paths/`).
- Same patch strategy for `target_gcs.paths.partitioned.smart_open.open`: use existing local patch or a conftest fixture that patches only that module and yields the mock.
- **Preserve** all assertions and test names; no regressions. Use conftest fixtures and test_helpers only.

## Testing Needed

- Run `loaders/target-gcs/tests/unit/paths/test_partitioned.py` and the full target-gcs test suite. All tests must pass with unchanged assertions and test names. Black-box behaviour preserved.
