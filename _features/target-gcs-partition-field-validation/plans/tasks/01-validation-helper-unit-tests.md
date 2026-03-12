# Task Plan: 01-validation-helper-unit-tests

## Overview

This task establishes the **test contract** for the partition-date-field schema validation helper. It creates a dedicated test module and adds unit tests that call `validate_partition_date_field_schema(stream_name, field_name, schema)`. The helper is **not** implemented in this task; tests are written first (TDD). Tests will fail (e.g. `ImportError` or assertion failures) until task 02 implements the helper. This task has no dependencies and is the first in the feature pipeline.

**Scope:** Add tests only. No production code under `target_gcs/` is added or modified.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/helpers/test_partition_schema.py` | **Create.** New test module containing all unit tests for `validate_partition_date_field_schema`. |

**No other files** are created or modified. The helper module and sink integration are implemented in later tasks.

---

## Test Strategy

### Import and test target

- Tests import: `from target_gcs.helpers import validate_partition_date_field_schema`.
- Until task 02 adds the helper and exports it from `target_gcs.helpers`, the test run will fail (e.g. `ImportError`). After implementation, tests validate behaviour; no assertion on call counts or logs (black-box).

### Test cases (from master testing.md and task doc)

| # | Scenario | Input | Expected |
|---|----------|--------|----------|
| 1 | Field missing from schema | `schema = {"properties": {"a": {"type": "string"}}}`, `field_name = "b"` | `ValueError`; message contains stream name, field name, and "not in schema" (or equivalent). |
| 2 | Null-only type | `schema = {"properties": {"x": {"type": "null"}}}`, `field_name = "x"` | `ValueError`; message contains "null-only" or "cannot be parsed to a date". |
| 3 | Null-only array type | `schema = {"properties": {"x": {"type": ["null"]}}}`, `field_name = "x"` | Same as #2. |
| 4 | Integer type | `schema = {"properties": {"x": {"type": "integer"}}}`, `field_name = "x"` | `ValueError`; message contains "non–date-parseable" (or equivalent). |
| 5 | Boolean type | `schema = {"properties": {"x": {"type": "boolean"}}}`, `field_name = "x"` | Same as #4. |
| 6 | String type (valid) | `schema = {"properties": {"x": {"type": "string"}}}`, `field_name = "x"` | No exception. |
| 7 | String with format date-time (valid) | `schema = {"properties": {"x": {"type": "string", "format": "date-time"}}}`, `field_name = "x"` | No exception. |
| 8 | Nullable string (valid) | `schema = {"properties": {"x": {"type": ["string", "null"]}}}`, `field_name = "x"` | No exception. |
| 9 | Empty or missing properties | `schema = {}` or `schema = {"properties": {}}`, `field_name = "any"` | `ValueError`; message contains "not in schema". |
| 10 | No properties key | `schema = {}`, `field_name = "any"` | `ValueError`; message contains "not in schema". |

### Assertion style

- **Failure cases (1–5, 9–10):** Use `pytest.raises(ValueError)` and assert that the exception message contains the stream name, field name, and the relevant reason substring. Do **not** assert the exact message string.
- **Success cases (6–8):** Call the helper; no exception. No assertion on return value (helper returns `None`).
- **Black-box:** Assert outcome only (exception type and message content). No assertions on call counts or log lines.

### Documentation per test

- Each test has a brief docstring or comment stating **what** is being tested and **why** (e.g. "Field missing from schema raises ValueError so users get a clear config error.").

---

## Implementation Order

1. **Create test module**  
   Create `loaders/target-gcs/tests/helpers/test_partition_schema.py`.

2. **Add imports and constants**  
   - `import pytest`  
   - `from target_gcs.helpers import validate_partition_date_field_schema`  
   - Define a fixed `stream_name` (e.g. `"test_stream"`) for use across tests, or pass per test as needed.

3. **Add failure-case tests (1–5, 9–10)**  
   For each failure scenario, add a test that builds the schema and field name, calls the helper inside `with pytest.raises(ValueError) as exc_info`, and asserts that the exception message contains the stream name, field name, and the expected reason substring. Use one test function per scenario with a descriptive name (e.g. `test_validate_partition_field_missing_from_schema_raises`).

4. **Add success-case tests (6–8)**  
   For each valid scenario, add a test that calls the helper with the given schema and field name; no exception expected. Name clearly (e.g. `test_validate_partition_field_string_type_succeeds`).

5. **Run tests**  
   From `loaders/target-gcs/`: `uv run pytest tests/helpers/test_partition_schema.py -v`. Expect failures (ImportError or assertion failures) until task 02.

6. **Lint and format**  
   Run `uv run ruff check .` and `uv run ruff format --check` from `loaders/target-gcs/`; fix any issues in the new file.

---

## Validation Steps

- [ ] File `loaders/target-gcs/tests/helpers/test_partition_schema.py` exists.
- [ ] All 10 scenarios above are covered by a distinct test.
- [ ] Failure tests use `pytest.raises(ValueError)` and assert message contains stream name, field name, and reason substring.
- [ ] Success tests call the helper and expect no exception.
- [ ] Each test has a brief docstring stating what is tested and why.
- [ ] From `loaders/target-gcs/`, `uv run pytest tests/helpers/test_partition_schema.py -v` runs (failing until task 02 is acceptable).
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass for the new file.

**Acceptance:** The test suite for the validation helper is in place and runnable. Task 02 will implement the helper so these tests pass.

---

## Documentation Updates

- **None** for this task. No user-facing docs or AI context changes are required; the tests document the expected behaviour of the helper. Component docs (e.g. `AI_CONTEXT_target-gcs.md`) will be updated in task 05 if needed.
