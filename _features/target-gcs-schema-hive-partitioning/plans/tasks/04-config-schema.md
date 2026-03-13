# Task Plan: 04 — Config schema (target)

## Overview

This task updates the target’s **JSON config schema only**. It adds the new `hive_partitioned` property (boolean, default false) and removes the legacy `partition_date_field` and `partition_date_format` properties from `GCSTarget.config_jsonschema`. No sink or helper code is changed; sink behaviour and tests that use partition config are updated in later tasks (05–08).

**Scope:** `loaders/target-gcs/target_gcs/target.py` and config-schema tests in `loaders/target-gcs/tests/test_sinks.py`.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/target.py` | Modify: add `hive_partitioned` Property; remove `partition_date_field` and `partition_date_format` Properties; update `key_naming_convention` description to reference `hive_partitioned` instead of `partition_date_field`. |
| `loaders/target-gcs/tests/test_sinks.py` | Modify: add tests that assert `hive_partitioned` is in schema (boolean, optional/default false); add tests that `partition_date_field` and `partition_date_format` are not in `config_jsonschema["properties"]`; remove or replace tests that assert the old properties exist (`test_config_schema_includes_partition_date_field`, `test_config_schema_includes_partition_date_format`, `test_config_validates_with_partition_date_field`). |

**No new files.** No changes to `sinks.py`, helpers, or `test_partition_key_generation.py` in this task (handled in 05–08).

---

## Test Strategy

- **TDD:** Add failing tests first, then implement schema changes until they pass.
- **Black-box:** Assert on the public config schema (properties, types, required array). Do not assert on call counts or logs.
- **Tests to add:**
  1. Config schema has `hive_partitioned` in `properties`; type is boolean (or list containing `"boolean"`); not in `required` (or has default false).
  2. Config schema does **not** have `partition_date_field` or `partition_date_format` in `properties`.
  3. Config that includes `hive_partitioned: true` or `hive_partitioned: false` validates and is readable from `target.config`.
- **Tests to remove or replace:**
  - `test_config_schema_includes_partition_date_field` → replace with assertion that `partition_date_field` is not in properties.
  - `test_config_schema_includes_partition_date_format` → replace with assertion that `partition_date_format` is not in properties.
  - `test_config_validates_with_partition_date_field` → replace with test that config with `hive_partitioned` (true/false) is valid.
- **Other tests:** Leave tests that call `build_sink(config={"partition_date_field": ...})` unchanged for this task; they will be updated in task 05/08 when the sink switches to `hive_partitioned`. After this task, those tests may still pass if the test config dict is passed through unchanged (schema only restricts what is declared, not what can be in the dict), but the **declared** schema must no longer include the old keys.

---

## Implementation Order

1. **Add new tests** in `test_sinks.py`:
   - `test_config_schema_includes_hive_partitioned`: assert `"hive_partitioned"` in properties; type boolean; not required.
   - `test_config_schema_omits_partition_date_field`: assert `"partition_date_field" not in properties`.
   - `test_config_schema_omits_partition_date_format`: assert `"partition_date_format" not in properties`.
   - `test_config_validates_with_hive_partitioned`: instantiate `GCSTarget` with `config={"bucket_name": "b", "hive_partitioned": True}` and with `hive_partitioned: False`; assert `target.config["hive_partitioned"]` (or default) as expected.
2. **Remove or replace** the three existing tests that assert the old partition properties exist or validate with them.
3. **Implement** in `target.py`:
   - Add `th.Property("hive_partitioned", th.BooleanType, required=False, default=False, description="When true, enable Hive partitioning from stream schema (x-partition-fields) or current date.")`.
   - Remove `th.Property("partition_date_field", ...)` and `th.Property("partition_date_format", ...)`.
   - Update `key_naming_convention` description to refer to `hive_partitioned` instead of `partition_date_field` (e.g. “When hive_partitioned is set and this is omitted, default is …”).
4. **Run tests:** `uv run pytest loaders/target-gcs/tests/test_sinks.py -v -k "config_schema or config_validates"` (and any other tests that reference config schema). Fix any failures.
5. **Lint/typecheck:** `uv run ruff check loaders/target-gcs/` and `uv run mypy target_gcs` from `loaders/target-gcs/`.

---

## Validation Steps

- [ ] New tests for `hive_partitioned` and for absence of `partition_date_field` / `partition_date_format` pass.
- [ ] Removed/replaced tests no longer reference the old properties; test suite passes.
- [ ] `GCSTarget.config_jsonschema["properties"]` contains `hive_partitioned` and does not contain `partition_date_field` or `partition_date_format`.
- [ ] Full target-gcs test suite passes: `uv run pytest` from `loaders/target-gcs/`.
- [ ] Ruff and MyPy pass with no new issues.
- [ ] No edits to `sinks.py`, helpers, or `test_partition_key_generation.py` in this task (those are later tasks).

---

## Documentation Updates

- **None** for this task. README and `meltano.yml` are updated in task 09. AI context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) will be updated when sink behaviour is changed in later tasks.

---

## Dependencies and Notes

- **Depends on:** None (config schema only; tasks 01–03 are not required for this task).
- **Blocks:** Task 05 (sink init validation) and later tasks expect the config schema to expose `hive_partitioned` and not the old partition keys.
- **Key wording:** Use the master plan description for `hive_partitioned`: “When true, enable Hive partitioning from stream schema (x-partition-fields) or current date.”
