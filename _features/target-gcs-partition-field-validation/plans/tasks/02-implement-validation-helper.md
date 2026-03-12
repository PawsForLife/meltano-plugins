# Task Plan: 02-implement-validation-helper

## Overview

This task **implements** the partition-date-field schema validation helper so that the unit tests added in task 01 pass. The helper is a pure function with no I/O or non-deterministic dependencies. It validates that the configured `partition_date_field` exists in the stream schema and has a date-parseable type (string, with or without date/date-time format; nullable string allowed; null-only and non-string types rejected). This task does not add new tests; it implements the contract already defined by task 01 tests and the master plan interfaces.

**Scope:** Create `target_gcs/helpers/partition_schema.py`, implement `validate_partition_date_field_schema`, and export it from `target_gcs.helpers`. Sink integration is task 04.

**Dependencies:** Task 01 (validation helper unit tests) must exist so implementation can be verified by running those tests.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/helpers/partition_schema.py` | **Create.** New module defining `validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None` with full logic and Google-style docstring. |
| `loaders/target-gcs/target_gcs/helpers/__init__.py` | **Modify.** Add `from .partition_schema import validate_partition_date_field_schema` and add `"validate_partition_date_field_schema"` to `__all__`. |

No other files are created or modified. Sink integration (calling the helper from `GCSSink.__init__`) is task 04.

---

## Test Strategy

- **No new tests in this task.** Task 01 added `tests/helpers/test_partition_schema.py`; this task implements the helper so those tests pass.
- **Run existing tests:** From `loaders/target-gcs/`, execute `uv run pytest tests/helpers/test_partition_schema.py -v`. All tests must pass after implementation.
- **Assertion contract:** Tests assert on outcomes only (exception type and message content: stream name, field name, and reason substring). Implementation must satisfy that contract; see [plans/master/testing.md](../master/testing.md) and task 01 plan for cases (field missing, null-only, integer/boolean, string/date-time/nullable string, empty or missing properties).

---

## Implementation Order

1. **Create the module**  
   Create `loaders/target-gcs/target_gcs/helpers/partition_schema.py`.

2. **Implement `validate_partition_date_field_schema`**  
   - **Signature:** `def validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None`.  
   - **Logic:**
     - Resolve `properties = schema.get("properties") or {}`.
     - If `field_name not in properties` → raise `ValueError` with message including `stream_name`, `field_name`, and reason `"is not in schema"` (or equivalent phrase used in task 01 tests).
     - Get `prop_schema = properties[field_name]`. Resolve `type`: if string, treat as single-type list `[type]`; if array, use as-is. Exclude `"null"` when deciding date-parseable.
     - If the only type is `"null"` (e.g. `type: "null"` or `type: ["null"]`) → raise `ValueError` with message including stream name, field name, and reason `"is null-only and cannot be parsed to a date"` (or equivalent).
     - If the set of non-null types does not include a date-parseable type → raise `ValueError` with message including stream name, field name, and reason `"has non–date-parseable type"` (or equivalent).
     - **Date-parseable:** allow `string` (with or without `format` in `{"date", "date-time"}`); allow nullable string (e.g. `["string", "null"]`). Reject `integer`, `number`, `boolean`, `array`, `object`, and null-only.
   - **Optional:** Use `singer_sdk.helpers._typing.get_datelike_property_type` or similar if available; still allow plain `string` without format.
   - **Docstring:** Google-style. Purpose: validate partition_date_field against stream schema. Args: `stream_name`, `field_name`, `schema`. Returns: `None`. Raises: `ValueError` with message including stream name, field name, and one of: not in schema, null-only, non–date-parseable type.

3. **Export from helpers**  
   In `target_gcs/helpers/__init__.py`, add:
   - `from .partition_schema import validate_partition_date_field_schema`
   - Append `"validate_partition_date_field_schema"` to `__all__`.

4. **Run tests**  
   From `loaders/target-gcs/`: `uv run pytest tests/helpers/test_partition_schema.py -v`. Fix implementation until all tests pass.

5. **Lint and typecheck**  
   From `loaders/target-gcs/`: `uv run ruff check .`, `uv run ruff format .` (or `--check` then fix), `uv run mypy target_gcs`. Resolve any issues.

---

## Validation Steps

- [ ] `loaders/target-gcs/target_gcs/helpers/partition_schema.py` exists and defines `validate_partition_date_field_schema`.
- [ ] `target_gcs/helpers/__init__.py` exports `validate_partition_date_field_schema` (import and `__all__`).
- [ ] All tests in `tests/helpers/test_partition_schema.py` pass: `uv run pytest tests/helpers/test_partition_schema.py -v`.
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass in `loaders/target-gcs/`.
- [ ] `uv run mypy target_gcs` passes in `loaders/target-gcs/`.

**Acceptance criteria:** All tests in `tests/helpers/test_partition_schema.py` pass; ruff and mypy pass.

---

## Documentation Updates

- **None** for this task. No user-facing docs or AI context changes. Component docs (e.g. `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) will be updated in task 05 if needed. The function’s docstring documents the public contract for the helper.
