# Task 03 — Helper exports

## Background

The sink will import `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema` from the helpers package. This task updates `helpers/__init__.py` so those functions are part of the public API. Depends on tasks 01 and 02 (implementations must exist).

## This Task

- **File:** `loaders/target-gcs/target_gcs/helpers/__init__.py`
  - Export `get_partition_path_from_schema_and_record` (from `partition_path`) and `validate_partition_fields_schema` (from `partition_schema`).
  - Add both to `__all__`.
  - If the sink and no other callers use `get_partition_path_from_record` and `validate_partition_date_field_schema`, remove them from exports (plan: no backward compatibility required; remove when unused).

## Testing Needed

- No new test file required. Verify that `from target_gcs.helpers import get_partition_path_from_schema_and_record, validate_partition_fields_schema` works (existing or new import tests; or covered by sink tests in later tasks).
