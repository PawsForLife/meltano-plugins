# Task 01 — Validator tests and implementation

## Background

Schema-driven Hive partitioning requires that every field listed in `x-partition-fields` exists in the stream schema, is required, and is non-nullable. This task adds `validate_partition_fields_schema` in `partition_schema.py` and has no dependencies on other feature tasks. Follow TDD: add tests first, then implement.

## This Task

- **File:** `loaders/target-gcs/target_gcs/helpers/partition_schema.py`
  - Add `validate_partition_fields_schema(stream_name: str, schema: dict, partition_fields: list[str]) -> None`.
  - For each field in `partition_fields`: ensure `field` is in `schema.get("properties", {})`; ensure `field` is in `schema.get("required", [])` (if `required` is not a list, raise); ensure the property type is not null-only (at least one non-null type).
  - On first failure raise `ValueError` with message including `stream_name`, `field`, and reason (e.g. "is not in schema", "must be required for the stream", "is null-only").
  - Keep or remove `validate_partition_date_field_schema` only according to current call sites; plan allows keeping it until sink is updated.
- **Interface:** See `plans/master/interfaces.md` — validator is pure: schema + list of field names → None or ValueError.

## Testing Needed

- **File:** `loaders/target-gcs/tests/helpers/test_partition_schema.py`
  - **Valid:** Schema with properties A, B; required [A, B]; partition_fields [A, B]; types string and number. Call validator; no exception.
  - **Missing field in properties:** partition_fields includes "C"; "C" not in schema["properties"]. Expect `ValueError` with stream name and "not in schema".
  - **Field not required:** required [A]; partition_fields [A, B]; B in properties but not in required. Expect `ValueError` "must be required".
  - **Required not a list:** schema["required"] = "A" or missing. Expect `ValueError`.
  - **Null-only type:** Property type "null" or ["null"]. Expect `ValueError` "null-only".
  - **Mixed optional and required:** required [A]; partition_fields [A, B]; B optional. Expect `ValueError` for B.
- Use `pytest.raises(ValueError)` and assert message contains `stream_name` and reason substring. No assertions on call counts or logs.
