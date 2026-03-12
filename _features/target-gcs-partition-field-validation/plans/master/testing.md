# Implementation Plan — Testing

## Test Strategy (TDD)

Tests are written **before** implementation. Run tests after adding the helper signature (they fail); implement until they pass. Follow black-box style: assert on outcomes (exception raised or not, exception type and message content), not on call counts or log lines.

## Tests to Write First

### 1. Validation helper — direct unit tests

**Location**: `loaders/target-gcs/tests/helpers/test_partition_schema.py` (new) or a dedicated section in `loaders/target-gcs/tests/helpers/test_partition_path.py`.

**Cases**:

| # | Scenario | Input (schema / field) | Expected |
|---|----------|------------------------|----------|
| 1 | Field missing from schema | `schema = {"properties": {"a": {"type": "string"}}}`; `field_name = "b"` | `ValueError` with message containing stream name, field name, “not in schema” |
| 2 | Null-only type | `schema = {"properties": {"x": {"type": "null"}}}`; `field_name = "x"` | `ValueError` with “null-only” (or “cannot be parsed to a date”) |
| 3 | Null-only array type | `schema = {"properties": {"x": {"type": ["null"]}}}`; `field_name = "x"` | Same as above |
| 4 | Integer type | `schema = {"properties": {"x": {"type": "integer"}}}`; `field_name = "x"` | `ValueError` with “non–date-parseable” (or equivalent) |
| 5 | Boolean type | `schema = {"properties": {"x": {"type": "boolean"}}}`; `field_name = "x"` | Same |
| 6 | String type (valid) | `schema = {"properties": {"x": {"type": "string"}}}`; `field_name = "x"` | No exception |
| 7 | String with format date-time (valid) | `schema = {"properties": {"x": {"type": "string", "format": "date-time"}}}`; `field_name = "x"` | No exception |
| 8 | Nullable string (valid) | `schema = {"properties": {"x": {"type": ["string", "null"]}}}`; `field_name = "x"` | No exception |
| 9 | Empty properties | `schema = {}` or `schema = {"properties": {}}`; `field_name = "any"` | `ValueError` “not in schema” |
| 10 | No properties key | `schema = {}`; `field_name = "any"` | `ValueError` “not in schema” |

**Assertions**: Use `pytest.raises(ValueError)` and, if needed, match message content (e.g. stream name, field name, and reason substring). Do not assert on exact message string to avoid brittleness; prefer “in” checks or regex for key phrases.

### 2. Sink integration tests

**Location**: `loaders/target-gcs/tests/test_sinks.py`.

**Setup**: Reuse or extend existing sink builder (e.g. `build_sink`) to accept `stream_name`, `schema`, and `config` including `partition_date_field`.

**Cases**:

| # | Scenario | Config | Schema | Expected |
|---|----------|--------|--------|----------|
| 1 | partition_date_field set, field missing | `partition_date_field: "dt"` | `{"properties": {"id": {}}}` | `ValueError` when constructing sink |
| 2 | partition_date_field set, field null-only | `partition_date_field: "dt"` | `{"properties": {"dt": {"type": "null"}}}` | `ValueError` when constructing sink |
| 3 | partition_date_field set, field integer | `partition_date_field: "dt"` | `{"properties": {"dt": {"type": "integer"}}}` | `ValueError` when constructing sink |
| 4 | partition_date_field set, field string | `partition_date_field: "dt"` | `{"properties": {"dt": {"type": "string"}}}` | Sink constructs successfully (no exception) |
| 5 | partition_date_field not set | no partition_date_field | any schema | Sink constructs successfully; no validation runs (no regression) |

**Assertions**: Construct `GCSSink(...)` (or use builder) with the given config and schema; either `with pytest.raises(ValueError): ...` or assert no exception. Do not assert on log or call counts.

### 3. Optional: message content

- One test that validation error message includes the stream name and field name (e.g. parse message and check substrings or use `match=` in `pytest.raises`).

## Integration and Regression

- Run the full target-gcs test suite after implementation. All existing tests must pass.
- Standard target tests (e.g. `test_core.py` with `get_target_test_class(GCSTargetWithMockStorage, ...)`) should still pass; default config typically does not set `partition_date_field`, so no behaviour change for that path.

## Test Execution

From `loaders/target-gcs/` with venv active:

```bash
uv run pytest tests/helpers/test_partition_schema.py tests/test_sinks.py -v
uv run pytest
```

Lint and typecheck:

```bash
uv run ruff check .
uv run ruff format --check
uv run mypy target_gcs
```
