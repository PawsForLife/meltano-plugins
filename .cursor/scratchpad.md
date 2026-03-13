# Pipeline Scratchpad

## Feature: restructure-target-gcs-tests

**Pipeline State:** Phase 1 Complete, Phase 2 Complete, Phase 3 Complete, Phase 4 Complete, Phase 5 Not started, Phase 6 Not started.

**Task Completion Status:** Task 01-rename-test-files completed, tests passing.

Task plan created: 02-merge-partition-key-tests-into-sinks at plans/tasks/02-merge-partition-key-tests-into-sinks.md

**Task plan created:** 01-rename-test-files at plans/tasks/01-rename-test-files.md

**Task plan created:** 05-verification-and-quality at plans/tasks/05-verification-and-quality.md

**Task plan created:** 03-optional-shared-sink-test-helpers at plans/tasks/03-optional-shared-sink-test-helpers.md

**Task plan created:** 04-update-ci-and-script-paths at plans/tasks/04-update-ci-and-script-paths.md

**Execution Order:** 01-rename-test-files.md, 02-merge-partition-key-tests-into-sinks.md, 03-optional-shared-sink-test-helpers.md, 04-update-ci-and-script-paths.md, 05-verification-and-quality.md

**Task count:** 5

**Plan location:** _features/restructure-target-gcs-tests/plans/master/

---

## Redundant tests in target-gcs (2025-03-13)

**Scope:** loaders/target-gcs tests only. No feature file; direct analysis.

**Findings:**

1. **Duplicate "valid hive schema constructs" (test_sinks.py)**
   - `test_sink_init_hive_partitioned_valid_x_partition_fields_succeeds` and `test_hive_partitioned_valid_schema_constructs_successfully` both: build_sink with hive_partitioned true and valid x-partition-fields (field in properties + required), assert sink constructs (e.g. stream_name).
   - **Action:** Remove one (e.g. the first); keep `test_hive_partitioned_valid_schema_constructs_successfully`.

2. **Duplicate "fallback date in key when no x-partition-fields" (test_sinks vs test_partition_key_generation)**
   - `test_sinks.test_hive_partitioned_true_no_x_partition_fields_key_contains_fallback_date` and `test_partition_key_generation.test_hive_partitioned_true_without_x_partition_fields_key_contains_fallback_date` both: hive_partitioned true, schema with no x-partition-fields, date_fn, assert key contains year=2024/month=03/day=11.
   - **Action:** Remove the one in test_partition_key_generation; keep the integration test in test_sinks.

**Not redundant (keep):**
- Unit tests in `test_partition_schema.py` vs sink-init validation in `test_sinks.py`: different levels (unit vs integration); both useful.
- Decimal/JSON: helper tests in `test_json_parsing.py` vs sink tests in `test_sinks.py`: unit vs integration.
- Duplicate helpers `build_sink` / `_key_from_open_call` in test_sinks and test_partition_key_generation: duplication of helpers, not of test cases; consolidation could be a separate refactor.
