# Background

The feature adds partition-date-field schema validation to target-gcs. Validation is implemented by a helper `validate_partition_date_field_schema(stream_name, field_name, schema)` that checks the field exists in the stream schema and has a date-parseable type. Per TDD and the plan, helper behaviour must be defined by tests first; the helper is not yet implemented. This task establishes the test contract so the next task can implement the helper to satisfy it.

**Dependencies:** None. This is the first task.

# This Task

- Create or extend the test module for the validation helper.
- **Location:** `loaders/target-gcs/tests/helpers/test_partition_schema.py` (new file). If the project prefers a single helpers test file, add a dedicated section in `loaders/target-gcs/tests/helpers/test_partition_path.py` instead.
- Add unit tests that call the validation helper (import from `target_gcs.helpers` or `target_gcs.helpers.partition_schema` once the helper exists; tests will fail until task 02 implements the helper).
- **Test cases (from plan testing.md):**
  1. **Field missing from schema:** `schema = {"properties": {"a": {"type": "string"}}}`, `field_name = "b"` → expect `ValueError` with message containing stream name, field name, and "not in schema" (or equivalent).
  2. **Null-only type:** `schema = {"properties": {"x": {"type": "null"}}}`, `field_name = "x"` → `ValueError` with "null-only" or "cannot be parsed to a date".
  3. **Null-only array type:** `schema = {"properties": {"x": {"type": ["null"]}}}`, `field_name = "x"` → same as above.
  4. **Integer type:** `schema = {"properties": {"x": {"type": "integer"}}}`, `field_name = "x"` → `ValueError` with "non–date-parseable" (or equivalent).
  5. **Boolean type:** `schema = {"properties": {"x": {"type": "boolean"}}}`, `field_name = "x"` → same.
  6. **String type (valid):** `schema = {"properties": {"x": {"type": "string"}}}`, `field_name = "x"` → no exception.
  7. **String with format date-time (valid):** `schema = {"properties": {"x": {"type": "string", "format": "date-time"}}}`, `field_name = "x"` → no exception.
  8. **Nullable string (valid):** `schema = {"properties": {"x": {"type": ["string", "null"]}}}`, `field_name = "x"` → no exception.
  9. **Empty or missing properties:** `schema = {}` or `schema = {"properties": {}}`, `field_name = "any"` → `ValueError` "not in schema".
  10. **No properties key:** `schema = {}`, `field_name = "any"` → `ValueError` "not in schema".
- Use `pytest.raises(ValueError)` for failure cases; assert message contains stream name, field name, and reason substring (avoid asserting exact message string). Follow black-box style: assert outcome only, not call counts or logs.
- Add a brief docstring or comment per test stating **what** is being tested and **why** (e.g. "Field missing from schema raises ValueError so users get a clear config error.").

**Acceptance criteria:** All listed scenarios have a test; tests run with `uv run pytest tests/helpers/test_partition_schema.py -v` (or the chosen path). Tests will fail until the helper is implemented in task 02.

# Testing Needed

- The tests added in this task *are* the test suite for the helper. No additional test file is required.
- Run `uv run pytest tests/helpers/test_partition_schema.py -v`; expect failures (missing helper or wrong behaviour) until task 02 is done.
