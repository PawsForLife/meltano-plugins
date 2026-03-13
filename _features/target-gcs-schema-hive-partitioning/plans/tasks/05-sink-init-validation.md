# Task Plan: 05 — Sink init and validation

## Overview

This task wires the sink to the new **hive partitioning** model: use `hive_partitioned` instead of `partition_date_field` everywhere, run **init-time validation** via `validate_partition_fields_schema` when `hive_partitioned` is true and the stream schema has non-empty `x-partition-fields`, set `_current_partition_path` when hive partitioning is enabled, and resolve partition path in the partition-by-field path via `get_partition_path_from_schema_and_record` (so the sink no longer depends on removed config keys). It ensures the sink works with the config schema from task 04 (no `partition_date_field` / `partition_date_format`) and the helpers from tasks 01 and 03.

**Scope:** `loaders/target-gcs/target_gcs/sinks.py` and sink init/config tests in `loaders/target-gcs/tests/test_sinks.py`. Optional touch to `test_partition_key_generation.py` only where tests still pass config with `partition_date_field` (those tests must be updated to use `hive_partitioned` and schema with `x-partition-fields` so they continue to pass).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | **Modify:** (1) Imports: add `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema` from `.helpers`; remove `get_partition_path_from_record` and `validate_partition_date_field_schema` from imports. (2) `__init__`: when `self.config.get("hive_partitioned")` and `self.schema.get("x-partition-fields")` is a non-empty list, call `validate_partition_fields_schema(self.stream_name, self.schema, self.schema["x-partition-fields"])`; set `_current_partition_path: str \| None = None` when `hive_partitioned` is true (same pattern as current partition_date_field). (3) Replace every `partition_date_field` check with `hive_partitioned`: `_get_effective_key_template`, `key_name` property, `process_record` dispatch, and init condition. (4) `_process_record_partition_by_field`: obtain partition path via `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`; remove use of `partition_date_field` and `partition_date_format` from config. (5) Docstrings/comments: refer to `hive_partitioned` and `x-partition-fields` where appropriate. |
| `loaders/target-gcs/tests/test_sinks.py` | **Modify:** (1) Add test: sink init with `hive_partitioned` true and schema `x-partition-fields: ["missing"]` but `"missing"` not in `properties` → expect `ValueError` on sink construction. (2) Add test: sink init with `hive_partitioned` true and schema `x-partition-fields: ["a"]` with `a` in `properties` and `required`, non-null type → no exception. (3) Replace tests that assert or use `partition_date_field` with `hive_partitioned` and schema: e.g. `_get_effective_key_template` returns hive default when `hive_partitioned` is true; update `test_partition_date_field_set_*` and `test_partition_date_field_unset_*` to use `hive_partitioned` and `x-partition-fields` (invalid cases → ValueError; valid/unset → success). (4) Remove or refactor tests that assumed `partition_date_field` in config schema (already removed in task 04). |
| `loaders/target-gcs/tests/test_partition_key_generation.py` | **Modify (minimal):** Update `build_sink` usage and any config passed to sinks so that partition-enabled tests use `hive_partitioned: true` and a schema with `x-partition-fields` (and matching `properties`/`required`) instead of `partition_date_field`. Ensure tests that assert on partition path or key still pass (same behaviour, different config and path resolution). |

**No new files.**

---

## Test Strategy

- **TDD:** Add the two new init tests first (invalid `x-partition-fields` → ValueError; valid → no exception), then implement init and validation in the sink until they pass. Then adjust existing partition-related tests to use `hive_partitioned` and schema; fix any regressions.
- **Black-box:** Assert on observable behaviour: sink construction raises or does not raise; key template and key name behaviour when `hive_partitioned` is true/false. Do not assert on call counts or log output.
- **Tests to add:**
  1. **Sink init with hive_partitioned and invalid x-partition-fields:** Config `hive_partitioned: true`, schema `x-partition-fields: ["missing"]`, `"missing"` not in `properties`. Expect `ValueError` when constructing `GCSSink` (e.g. `pytest.raises(ValueError, build_sink, ...)` or equivalent). Message should include stream name and reason (e.g. not in schema).
  2. **Sink init with hive_partitioned and valid x-partition-fields:** Config `hive_partitioned: true`, schema with `x-partition-fields: ["a"]`, `properties: { "a": { "type": "string" } }`, `required: ["a"]`. Construct sink; no exception.
- **Tests to update:** Replace `partition_date_field` with `hive_partitioned` and provide schema with `x-partition-fields` where partition behaviour is under test (e.g. effective key template returns `DEFAULT_KEY_NAMING_CONVENTION_HIVE` when `hive_partitioned` is true; existing partition-date-field validation tests become hive partition validation tests with valid/invalid `x-partition-fields`).
- **Exception tests:** Use `pytest.raises(ValueError)` and optionally assert that the exception message contains the stream name and a reason substring (e.g. "not in schema", "must be required").

---

## Implementation Order

1. **Add new tests** in `test_sinks.py`:
   - `test_sink_init_hive_partitioned_invalid_x_partition_fields_raises_value_error`: build_sink with `config={"hive_partitioned": True}`, schema `{"x-partition-fields": ["missing"], "properties": {}, "required": []}`. Expect `ValueError`.
   - `test_sink_init_hive_partitioned_valid_x_partition_fields_succeeds`: build_sink with `config={"hive_partitioned": True}`, schema with `x-partition-fields: ["a"]`, `a` in properties (type string) and in required. No exception.
2. **Implement in `sinks.py`:**
   - Update imports: from `.helpers` import `get_partition_path_from_schema_and_record`, `validate_partition_fields_schema`; remove `get_partition_path_from_record`, `validate_partition_date_field_schema`.
   - In `__init__`: replace condition `if self.config.get("partition_date_field")` with `if self.config.get("hive_partitioned")`. When true, set `self._current_partition_path = None`. When true and `self.schema.get("x-partition-fields")` is a non-empty list, call `validate_partition_fields_schema(self.stream_name, self.schema, self.schema["x-partition-fields"])`.
   - In `_get_effective_key_template`: use `self.config.get("hive_partitioned")` instead of `partition_date_field`; when truthy return `DEFAULT_KEY_NAMING_CONVENTION_HIVE`, else user template or `DEFAULT_KEY_NAMING_CONVENTION`.
   - In `key_name` property: use `self.config.get("hive_partitioned")` instead of `partition_date_field`.
   - In `process_record`: dispatch on `self.config.get("hive_partitioned")` instead of `partition_date_field`.
   - In `_process_record_partition_by_field`: compute `partition_path = get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`; remove `partition_date_format` and `partition_date_field` from config reads.
   - Update class and method docstrings to refer to `hive_partitioned` and `x-partition-fields` where relevant.
3. **Update existing tests** in `test_sinks.py` that use `partition_date_field` or assert on partition-date-field validation: switch to `hive_partitioned` and schema with `x-partition-fields`; adjust expected exceptions for invalid schema (e.g. field not in properties, not required, null-only) to still expect `ValueError`.
4. **Update `test_partition_key_generation.py`:** Change any `build_sink(config={"partition_date_field": ...})` (and schema) to `hive_partitioned: true` and schema with `x-partition-fields` and matching properties/required so key and partition path behaviour tests still pass.
5. **Run tests:** `uv run pytest loaders/target-gcs/tests/test_sinks.py loaders/target-gcs/tests/test_partition_key_generation.py -v`. Fix regressions.
6. **Lint/typecheck:** `uv run ruff check loaders/target-gcs/` and `uv run mypy target_gcs` from `loaders/target-gcs/`.

---

## Validation Steps

- [ ] New tests for sink init with invalid/valid `x-partition-fields` pass.
- [ ] All references to `partition_date_field` and `partition_date_format` are removed from `sinks.py`; partition enablement uses `hive_partitioned`; path resolution uses `get_partition_path_from_schema_and_record` with `DEFAULT_PARTITION_DATE_FORMAT`.
- [ ] Sink init calls `validate_partition_fields_schema` when `hive_partitioned` is true and `x-partition-fields` is present and non-empty.
- [ ] Existing partition-related tests updated to use `hive_partitioned` and schema; full test suite passes (`uv run pytest` from `loaders/target-gcs/`).
- [ ] Ruff and MyPy pass with no new issues.
- [ ] No remaining imports of `get_partition_path_from_record` or `validate_partition_date_field_schema` in `sinks.py` (helpers may still define them for backward compatibility or removal in a later task).

---

## Documentation Updates

- **None** for this task. README and Meltano docs are updated in task 09. If AI context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) is updated in a later task, it will describe `hive_partitioned` and init validation with `x-partition-fields`.

---

## Dependencies and Notes

- **Depends on:** Tasks 01 (validator `validate_partition_fields_schema`), 03 (exports of `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema`), 04 (config schema with `hive_partitioned` and without `partition_date_field` / `partition_date_format`). Task 02 (path builder) is required for the helpers used here.
- **Blocks:** Task 06 (sink record processing) and 07 (process_record dispatch) may refine or extend the same code paths; 08 (sink and key tests) will add further black-box tests.
- **Init validation rule:** Only call `validate_partition_fields_schema` when both `hive_partitioned` is true **and** `schema.get("x-partition-fields")` is a non-empty list. When `hive_partitioned` is true and `x-partition-fields` is missing or empty, use current date for partition path (no schema validation of partition fields).
- **Constant:** Use `DEFAULT_PARTITION_DATE_FORMAT` from `sinks.py` when calling `get_partition_path_from_schema_and_record`; config no longer supplies `partition_date_format` (removed in task 04).
