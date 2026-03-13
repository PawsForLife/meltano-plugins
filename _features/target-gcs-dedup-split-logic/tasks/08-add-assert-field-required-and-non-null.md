# Task 08: Add _assert_field_required_and_non_null_type and refactor partition_schema validators

## Background

`validate_partition_fields_schema` and `validate_partition_date_field_schema` in `partition_schema.py` share the pattern: field must be in properties, in required, and have a non-null type. This task extracts that into a module-private helper and refactors both public validators to use it. No dependency on sinks.py tasks; can be done in parallel with 02–07 from a dependency perspective, but placed after 07 in execution order for consistency.

## This Task

- In `loaders/target-gcs/target_gcs/helpers/partition_schema.py`:
  - Implement `_assert_field_required_and_non_null_type(stream_name: str, field_name: str, schema: dict) -> None`: (1) raise `ValueError` if `schema["required"]` is not a list; (2) raise if `field_name` not in `schema.get("properties") or {}`; (3) raise if `field_name` not in required; (4) get property schema, `raw_type = prop_schema.get("type")`; if None, raise; (5) resolve type as single or list, compute non_null types (filter out "null"); if no non-null type, raise. Reuse existing error message style (stream name, field name, reason). Do not export from `helpers/__init__.py`.
  - Refactor `validate_partition_fields_schema`: for each partition field, call `_assert_field_required_and_non_null_type(stream_name, field_name, schema)`, then perform any per-field checks that remain.
  - Refactor `validate_partition_date_field_schema`: call `_assert_field_required_and_non_null_type(stream_name, field_name, schema)`, then perform the date-parseable check (or equivalent) that remains.
- Add a Google-style docstring for `_assert_field_required_and_non_null_type` (purpose, Args, Raises).

**Acceptance criteria:** Both public validators delegate "in properties, required, non-null type" to the helper; exception types and messages remain consistent; no duplicated validation logic.

## Testing Needed

- Run existing `test_partition_schema.py` and sink-init tests in `test_sinks.py`; all must pass. If any branch of the new helper (e.g. "required is not a list", "field not in properties", "no type", "only null type") is not covered by existing tests, add a test first (TDD) that expects `ValueError` with appropriate message (e.g. `pytest.raises(ValueError)` and assert on message or stream/field), then implement the helper. Black-box: assert on raised exception and message content, not on call counts.
