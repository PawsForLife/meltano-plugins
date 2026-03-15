# Pipeline Scratchpad

## Feature: target-gcs-conftest-restructure

- **Pipeline State:** Phase 4 (Per-task planning) complete; Phase 5 (Implementation) in progress.
- **Task Completion Status:** Task 01-create-test-helpers completed, tests passing.
- **Task count:** 8.
- **Execution Order:** 01-create-test-helpers.md, 02-create-conftest.md, 03-refactor-test-target.md, 04-refactor-test-sinks.md, 05-refactor-test-simple.md, 06-refactor-test-dated.md, 07-refactor-test-partitioned.md, 08-optional-refactor-test-base.md.
- **Plan location:** `_features/target-gcs-conftest-restructure/plans/master/` (overview.md, architecture.md, interfaces.md, implementation.md, testing.md, dependencies.md, documentation.md).
- **Task plan created:** 01-create-test-helpers at plans/tasks/01-create-test-helpers.md.
- **Task plan created:** 04-refactor-test-sinks at plans/tasks/04-refactor-test-sinks.md.
- **Task plan created:** 03-refactor-test-target at plans/tasks/03-refactor-test-target.md.
- **Task plan created:** 02-create-conftest at plans/tasks/02-create-conftest.md.
- **Task plan created:** 07-refactor-test-partitioned at plans/tasks/07-refactor-test-partitioned.md.
- **Task plan created:** 05-refactor-test-simple at plans/tasks/05-refactor-test-simple.md.
- **Task plan created:** 06-refactor-test-dated at plans/tasks/06-refactor-test-dated.md.
- **Task plan created:** 08-optional-refactor-test-base at plans/tasks/08-optional-refactor-test-base.md.

**Key decisions (Phase 2):**
- Conftest holds fixtures (sample_config, fixed_time_fn, fixed_date_fn, mock_storage_client, mock_open_handle, patch_all_pattern_modules) and factory helpers (build_sink, build_simple_path, build_dated_path, build_partitioned_path); test_helpers holds the pure function key_from_open_call for use by tests and optional conftest usage.
- patch_all_pattern_modules is a fixture that patches smart_open.open (×3) and Client and yields (open_mock, client_mock) for sink tests; path tests may keep per-file patches or use optional per-pattern fixtures.
- No new external deps (pytest + unittest.mock only); no new test files for conftest unless non-trivial helpers need tests; black-box behaviour and one-test-file-per-source-module preserved.

**Phase 1 Research Summary (handoff):**
- **Output directory:** `_features/target-gcs-conftest-restructure/planning/` (impacted-systems.md, new-systems.md, possible-solutions.md, selected-solution.md).
- **Key findings:** (1) Duplication: `_key_from_open_call` in four files; `build_sink`, `_patch_all_pattern_modules`, default config and FIXED_DATE in test_sinks; path builders and same default config in test_simple, test_dated, test_partitioned; test_target has its own SAMPLE_CONFIG. (2) Patch usage: test_sinks uses a single context that patches smart_open.open (×3) and Client; each path test file patches only its pattern’s smart_open.open. (3) No existing conftest under loaders/target-gcs/tests. (4) External plugins (pytest-gcs, pytest-google-cloud-storage) are for real/fake GCS and are overkill for unit tests; pytest-mock is optional and does not remove duplication.
- **Selected solution:** Internal conftest + fixtures. Add `loaders/target-gcs/tests/conftest.py` with constants (SAMPLE_CONFIG, FIXED_DATE), fixtures (sample_config, fixed_time_fn, fixed_date_fn, mock_storage_client, mock_open_handle, patch_all_pattern_modules), and factory functions (build_sink, build_simple_path, build_dated_path, build_partitioned_path). Add `loaders/target-gcs/tests/test_helpers.py` with `key_from_open_call(call_args)`. Refactor tests to use these fixtures and helpers; prefer injected mocks where code allows; keep a single patch context in conftest for smart_open and Client. All existing tests must pass with unchanged assertions.
