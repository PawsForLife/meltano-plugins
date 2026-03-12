# Background

The sink must call the validation helper in `GCSSink.__init__` when `partition_date_field` is set. Integration behaviour is: constructing a sink with `partition_date_field` and an invalid schema (missing field, null-only, or non–date-parseable type) must raise `ValueError`; valid schema or no `partition_date_field` must allow construction. Per TDD, these tests are written before wiring the helper into the sink (task 04).

**Dependencies:** Task 02 (validation helper implemented and exported). The helper is called by the sink; tests construct the sink with config and schema, so the helper must exist and be importable.

# This Task

- **Location:** `loaders/target-gcs/tests/test_sinks.py`.
- Extend the test suite with sink-level tests that build a sink (using existing `build_sink` or equivalent) with config and schema. Extend the test builder if needed to accept an optional `schema` (and optionally `stream_name`) so tests can pass schemas that have or lack the partition field with specific types.
- **Test cases (from plan testing.md):**
  1. **partition_date_field set, field missing:** config `partition_date_field: "dt"`, schema `{"properties": {"id": {}}}` → `ValueError` when constructing sink.
  2. **partition_date_field set, field null-only:** config `partition_date_field: "dt"`, schema `{"properties": {"dt": {"type": "null"}}}` → `ValueError` when constructing sink.
  3. **partition_date_field set, field integer:** config `partition_date_field: "dt"`, schema `{"properties": {"dt": {"type": "integer"}}}` → `ValueError` when constructing sink.
  4. **partition_date_field set, field string (valid):** config `partition_date_field: "dt"`, schema `{"properties": {"dt": {"type": "string"}}}` → sink constructs successfully (no exception).
  5. **partition_date_field not set:** no `partition_date_field` in config, any schema → sink constructs successfully; no regression.
- Use `pytest.raises(ValueError)` for failure cases; no assertion on log or call counts (black-box). Optionally add one test that the raised `ValueError` message includes stream name and field name.
- Add brief docstrings/comments per test stating what is being tested and why.

**Acceptance criteria:** All five scenarios have a test. Tests that expect `ValueError` will fail until task 04 adds the validation call in the sink; the valid and no-config cases may pass or fail depending on current sink behaviour.

# Testing Needed

- Run `uv run pytest tests/test_sinks.py -v` and execute the new tests. After task 04, all must pass.
- Do not assert on internal call counts or log lines; assert only on exception type and optionally message content.
