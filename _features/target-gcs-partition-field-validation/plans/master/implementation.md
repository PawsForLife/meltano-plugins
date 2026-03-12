# Implementation Plan — Implementation

## Implementation Order

1. **Tests first (TDD)**: Add tests for the validation helper and for the sink with `partition_date_field` and various schemas. See [testing.md](testing.md). Run tests; they fail until implementation exists.
2. **Helper**: Implement `validate_partition_date_field_schema` in the chosen module; export and use from sink.
3. **Sink integration**: In `GCSSink.__init__`, after `super().__init__` and existing attribute setup, call the helper when `partition_date_field` is set.
4. **Lint/typecheck**: Run `ruff check .`, `ruff format --check`, `mypy target_gcs` from `loaders/target-gcs/`. Fix any issues.
5. **Regression**: Ensure all existing tests pass; no new failing tests except those explicitly marked as expected failure.

## Files to Create or Modify

### New or extended module for validation

- **Option A — New file**: `loaders/target-gcs/target_gcs/helpers/partition_schema.py`
  - Define `validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None`.
  - Implement: resolve `properties`; check presence; check null-only; check date-parseable type (allow string / string+null / date-like format; reject the rest).
  - Add `__all__` or ensure the function is importable from `target_gcs.helpers` (e.g. in `target_gcs/helpers/__init__.py` if present).
- **Option B — In partition_path.py**: Add `validate_partition_date_field_schema` in `loaders/target-gcs/target_gcs/helpers/partition_path.py`. Keep `get_partition_path_from_record` unchanged. Export from helpers so sink can import from one place.

Recommendation: **Option A** keeps schema validation separate from path resolution; if the codebase prefers fewer files, Option B is acceptable.

### Sink integration

- **File**: `loaders/target-gcs/target_gcs/sinks.py`
  - Add import: `from .helpers import ... validate_partition_date_field_schema` (or from `.helpers.partition_schema` depending on option).
  - In `GCSSink.__init__`, after the block that sets `_current_partition_path` when `partition_date_field` is set, add:
    - If `self.config.get("partition_date_field")`: call `validate_partition_date_field_schema(self.stream_name, self.config["partition_date_field"], self.schema)`.
  - No change to `process_record`, `_build_key_for_record`, or other methods.

### Tests

- **Helper tests**: New or existing file under `loaders/target-gcs/tests/helpers/` (e.g. `test_partition_schema.py` or extend `test_partition_path.py` with a section for schema validation). See [testing.md](testing.md).
- **Sink tests**: Extend `loaders/target-gcs/tests/test_sinks.py` with cases that build a sink with `partition_date_field` and a given schema; assert `ValueError` when invalid and no exception when valid.

## Code Organization and Structure

- Validation logic is pure: no I/O, no global state, no non-deterministic calls. Type hints on the helper: `stream_name: str`, `field_name: str`, `schema: dict`, return `None`.
- Error messages: use f-strings or format with stream name, field name, and one of the three reason strings so tests and users see a consistent format.
- No dependency injection needed for the helper beyond the three arguments; schema and config are already available on the sink.

## Implementation Details for “Date-parseable”

- Normalize `type`: if `type` is a string, treat as single-type list `[type]`; if array, use as-is. Exclude `"null"` when deciding “date-parseable.”
- **Allow** if any remaining type is `"string"` (with or without `format` in `{"date", "date-time"}`). Optional: use `singer_sdk.helpers._typing.get_datelike_property_type(prop_schema)` or similar if available and if it returns a value for string with date/date-time format; still allow plain `string`.
- **Reject** if only type is `"null"` (already handled above).
- **Reject** if all non-null types are in `{"integer", "number", "boolean", "array", "object"}` (or not string and not date-like).
- **anyOf/oneOf**: For minimal scope, treat property as date-parseable if the top-level `type` (or first branch that is not null-only) includes string or date-like. Full anyOf/oneOf resolution can be a follow-up; document that complex schemas may be validated conservatively.

## Dependency Injection

- No new injectable dependencies. The sink already receives `schema` and `config`; the helper receives them as arguments. No `time_fn` or `date_fn` in the validation path.
