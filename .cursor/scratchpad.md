# Pipeline Scratchpad

## Feature: target-gcs-dedup-split-logic

**Pipeline State:** Phase 1–4 Complete; Phase 5–6 Not started.
**Task Completion Status:** Task 01-unify-partition-date-format-constant completed, tests passing. Task 02-add-flush-and-close-handle completed, tests passing. Task 03-add-apply-key-prefix-and-normalize completed, tests passing. Task 04-add-write-record-as-jsonl completed, tests passing.
**Task count:** 9.
**Execution Order:** 01-unify-partition-date-format-constant → 02-add-flush-and-close-handle → 03-add-apply-key-prefix-and-normalize → 04-add-write-record-as-jsonl → 05-add-maybe-rotate-if-at-limit → 06-add-compute-non-hive-key → 07-add-init-hive-partitioning → 08-add-assert-field-required-and-non-null → 09-update-docstrings-and-ai-context.
**Ordered task file names:** 01-unify-partition-date-format-constant.md, 02-add-flush-and-close-handle.md, 03-add-apply-key-prefix-and-normalize.md, 04-add-write-record-as-jsonl.md, 05-add-maybe-rotate-if-at-limit.md, 06-add-compute-non-hive-key.md, 07-add-init-hive-partitioning.md, 08-add-assert-field-required-and-non-null.md, 09-update-docstrings-and-ai-context.md.

**Phase 1 Research (output):** `_features/target-gcs-dedup-split-logic/planning/`

**Key findings:** Duplications: (1) handle flush+close in `_rotate_to_new_chunk` and `_close_handle_and_clear_state` in `sinks.py`, (2) key prefix + normalize in `_build_key_for_record` and `key_name`, (3) orjson.dumps + write in both record-processing methods, (4) rotate-if-at-limit block in both, (5) `DEFAULT_PARTITION_DATE_FORMAT` in `sinks.py` and `helpers/partition_path.py`, (6) shared “field in properties, required, non-null type” pattern in `validate_partition_fields_schema` and `validate_partition_date_field_schema` in `partition_schema.py`. Switch points: (1) `key_name` (hive vs non-hive), (2) `GCSSink.__init__` hive setup; `process_record` already split.

**Selected solution:** Unify via new sink-private methods (`_flush_and_close_handle`, `_apply_key_prefix_and_normalize`, `_write_record_as_jsonl`, `_maybe_rotate_if_at_limit`, `_compute_non_hive_key`, `_init_hive_partitioning`), single constant in `partition_path.py`, and shared `_assert_field_required_and_non_null_type` in `partition_schema.py`; split non-hive key and hive init into those named functions.

**Phase 2 Plan (output):** `_features/target-gcs-dedup-split-logic/plans/master/` — overview, architecture, interfaces, implementation, testing, dependencies, documentation.

Task plan created: 01-unify-partition-date-format-constant at plans/tasks/01-unify-partition-date-format-constant.md
Task plan created: 02-add-flush-and-close-handle at plans/tasks/02-add-flush-and-close-handle.md

**Key decisions:**
- Implementation order: constant + flush/close first, then key/write/rotate helpers, then `_compute_non_hive_key` and `_init_hive_partitioning`, then partition_schema helper; keeps call sites valid at each step.
- No new files or packages; all new logic lives in existing `sinks.py` and `helpers/partition_schema.py`; constant single-sourced in `partition_path.py`.
- Tests: existing suite is regression gate; add unit tests only for new helpers not fully covered by current black-box tests (e.g. edge cases for prefix/normalize or schema assertion).

Task plan created: 03-add-apply-key-prefix-and-normalize at plans/tasks/03-add-apply-key-prefix-and-normalize.md
Task plan created: 04-add-write-record-as-jsonl at plans/tasks/04-add-write-record-as-jsonl.md
Task plan created: 05-add-maybe-rotate-if-at-limit at plans/tasks/05-add-maybe-rotate-if-at-limit.md
Task plan created: 06-add-compute-non-hive-key at plans/tasks/06-add-compute-non-hive-key.md
Task plan created: 07-add-init-hive-partitioning at plans/tasks/07-add-init-hive-partitioning.md
Task plan created: 08-add-assert-field-required-and-non-null at plans/tasks/08-add-assert-field-required-and-non-null.md
Task plan created: 09-update-docstrings-and-ai-context at plans/tasks/09-update-docstrings-and-ai-context.md

---

## Redundant tests in target-gcs (2025-03-13)

**Scope:** loaders/target-gcs tests only. No feature file; direct analysis.

**Findings:**

1. **Duplicate “valid hive schema constructs” (test_sinks.py)**
   - `test_sink_init_hive_partitioned_valid_x_partition_fields_succeeds` and `test_hive_partitioned_valid_schema_constructs_successfully` both: build_sink with hive_partitioned true and valid x-partition-fields (field in properties + required), assert sink constructs (e.g. stream_name).
   - **Action:** Remove one (e.g. the first); keep `test_hive_partitioned_valid_schema_constructs_successfully`.

2. **Duplicate “fallback date in key when no x-partition-fields” (test_sinks vs test_partition_key_generation)**
   - `test_sinks.test_hive_partitioned_true_no_x_partition_fields_key_contains_fallback_date` and `test_partition_key_generation.test_hive_partitioned_true_without_x_partition_fields_key_contains_fallback_date` both: hive_partitioned true, schema with no x-partition-fields, date_fn, assert key contains year=2024/month=03/day=11.
   - **Action:** Remove the one in test_partition_key_generation; keep the integration test in test_sinks.

**Not redundant (keep):**
- Unit tests in `test_partition_schema.py` vs sink-init validation in `test_sinks.py`: different levels (unit vs integration); both useful.
- Decimal/JSON: helper tests in `test_json_parsing.py` vs sink tests in `test_sinks.py`: unit vs integration.
- Duplicate helpers `build_sink` / `_key_from_open_call` in test_sinks and test_partition_key_generation: duplication of helpers, not of test cases; consolidation could be a separate refactor.
