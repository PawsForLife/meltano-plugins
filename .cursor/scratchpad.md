# Pipeline Scratchpad

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
