# Background

Task 01 added unit tests for `validate_partition_date_field_schema`. This task implements the helper so those tests pass. The helper is a pure function with no I/O or non-deterministic dependencies; it validates that the configured partition date field exists in the stream schema and has a date-parseable type.

**Dependencies:** Task 01 (validation helper unit tests) must exist so implementation can be verified.

# This Task

- **Create module:** `loaders/target-gcs/target_gcs/helpers/partition_schema.py`.
- **Implement:** `validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None`.
  - Resolve `properties = schema.get("properties") or {}`.
  - If `field_name not in properties` → raise `ValueError` with message including stream name, field name, and reason "is not in schema".
  - Get `prop_schema = properties[field_name]`. Resolve `type` (string or array). If the only type is `"null"` → raise `ValueError` with "is null-only and cannot be parsed to a date".
  - If the set of types (excluding null) does not include a date-parseable type → raise `ValueError` with "has non–date-parseable type".
  - **Date-parseable:** allow `string` (with or without `format` in `{"date", "date-time"}`); allow nullable string (e.g. `["string", "null"]`). Reject `integer`, `number`, `boolean`, `array`, `object`, and null-only.
  - Normalize `type`: if string treat as `[type]`; exclude `"null"` when deciding date-parseable. Optional: use `singer_sdk.helpers._typing` (e.g. `get_datelike_property_type`) if available; still allow plain `string`.
- **Export:** Add `validate_partition_date_field_schema` to `target_gcs/helpers/__init__.py` (and `__all__` if used) so the sink can import from `target_gcs.helpers`.
- Add a Google-style docstring: purpose (validate partition_date_field against stream schema); args (stream_name, field_name, schema); return (None); raises (ValueError with message including stream name, field name, and one of: not in schema, null-only, non–date-parseable type).
- **Lint/typecheck:** Run `ruff check .`, `ruff format`, `mypy target_gcs` from `loaders/target-gcs/` and fix any issues.

**Acceptance criteria:** All tests in `tests/helpers/test_partition_schema.py` pass; ruff and mypy pass.

# Testing Needed

- Run `uv run pytest tests/helpers/test_partition_schema.py -v` — all tests must pass.
- Run `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy target_gcs` from `loaders/target-gcs/`.
