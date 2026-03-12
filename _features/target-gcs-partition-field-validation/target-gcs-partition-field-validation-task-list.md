# Task List: target-gcs-partition-field-validation

Feature adds partition-date-field schema validation to target-gcs: when `partition_date_field` is set, the sink validates at init that the field exists in the stream schema and has a date-parseable type; invalid config raises `ValueError` with stream name, field name, and reason.

## Execution Order and Dependencies

| # | Task file | Summary | Depends on |
|---|-----------|---------|------------|
| 01 | `tasks/01-validation-helper-unit-tests.md` | Add unit tests for `validate_partition_date_field_schema` (TDD; tests first) | — |
| 02 | `tasks/02-implement-validation-helper.md` | Implement helper in `partition_schema.py`, export from helpers | 01 |
| 03 | `tasks/03-sink-integration-tests.md` | Add sink-level tests (config + schema → ValueError or success) | 02 |
| 04 | `tasks/04-integrate-validation-into-sink.md` | Call validation helper from `GCSSink.__init__` when `partition_date_field` set | 02, 03 |
| 05 | `tasks/05-documentation-and-changelog.md` | Update AI context, CHANGELOG, and optional user docs | 01–04 |

## Interface Requirements

- **Helper:** `validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None`. Raises `ValueError` with message including stream name, field name, and one of: "not in schema", "null-only and cannot be parsed to a date", "has non–date-parseable type". No new public API; config and Singer message contracts unchanged.
- **Sink:** No signature change; call helper after `super().__init__` and after setting `_current_partition_path` when `partition_date_field` is set.

## Development Practices

- TDD: tests for helper (01) and sink behaviour (03) written before implementation (02, 04).
- Black-box tests: assert exception or success and message content; no call-count or log assertions.
- No new models; validation uses existing schema dict. No new dependency injection.

## Verification

- After 02: `uv run pytest tests/helpers/test_partition_schema.py -v` passes; ruff/mypy pass.
- After 04: `uv run pytest tests/helpers/test_partition_schema.py tests/test_sinks.py -v` and full `uv run pytest` pass; no regression.
- After 05: AI context and CHANGELOG updated; docs match implementation.
