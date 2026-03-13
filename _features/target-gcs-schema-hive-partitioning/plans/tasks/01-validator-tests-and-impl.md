# Task Plan: 01 — Validator tests and implementation

## Overview

This task adds the schema-driven Hive partition validator `validate_partition_fields_schema` to `partition_schema.py` and its unit tests. It has no dependencies on other feature tasks. The validator ensures every field in `x-partition-fields` exists in the stream schema, is required, and is non-nullable. Existing `validate_partition_date_field_schema` is **kept** (sink still uses it); removal is deferred to a later task when the sink is updated to use the new validator.

**Scope:** Helper only. No config, sink, or path-builder changes.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/helpers/test_partition_schema.py` | **Modify.** Add tests for `validate_partition_fields_schema` (see Test Strategy). Keep existing tests for `validate_partition_date_field_schema`. |
| `loaders/target-gcs/target_gcs/helpers/partition_schema.py` | **Modify.** Add `validate_partition_fields_schema(stream_name: str, schema: dict, partition_fields: list[str]) -> None`. Do not remove `validate_partition_date_field_schema`. |
| `loaders/target-gcs/target_gcs/helpers/__init__.py` | **Modify.** Export `validate_partition_fields_schema` and add to `__all__`. |

---

## Test Strategy

**TDD:** Add tests first in `test_partition_schema.py`, then implement until they pass. Use `pytest.raises(ValueError)` for failure cases; assert message contains `stream_name` and reason substring. No assertions on call counts or logs (black-box).

| Test | What | Why |
|------|------|-----|
| **Valid — all fields in properties, required, non-nullable** | Schema: `properties` A, B (e.g. string, number); `required` [A, B]; `partition_fields` [A, B]. Call validator; no exception. | Ensures valid schema passes. |
| **Missing field in properties** | `partition_fields` includes "C"; "C" not in `schema["properties"]`. Expect `ValueError` with stream name and "not in schema". | Rejects field not in schema. |
| **Field not required** | `required` [A]; `partition_fields` [A, B]; B in properties but not in required. Expect `ValueError` "must be required". | Ensures partition fields are required. |
| **Required not a list** | `schema["required"] = "A"` or missing. Expect `ValueError`. | Ensures schema shape is valid. |
| **Null-only type** | Property type `"null"` or `["null"]`. Expect `ValueError` "null-only". | Ensures non-nullable. |
| **Mixed optional and required** | `required` [A]; `partition_fields` [A, B]; B optional. Expect `ValueError` for B. | Covers typical failure. |

Import: add `from target_gcs.helpers import validate_partition_fields_schema` (or import from `partition_schema` if preferred for tests). Reuse `STREAM_NAME` or equivalent constant.

---

## Implementation Order

1. **Add tests** in `loaders/target-gcs/tests/helpers/test_partition_schema.py` for `validate_partition_fields_schema` per Test Strategy (valid case + five failure cases). Run pytest; tests fail (no implementation yet).
2. **Implement** `validate_partition_fields_schema` in `loaders/target-gcs/target_gcs/helpers/partition_schema.py`:
   - For each `field` in `partition_fields`: check `field` in `schema.get("properties", {})`; check `field` in `schema.get("required", [])` (if `required` is not a list, raise); check property type is not null-only (at least one non-null type in `type` or union).
   - On first failure raise `ValueError` with message including `stream_name`, `field`, and reason (e.g. "is not in schema", "must be required for the stream", "is null-only").
   - Reuse patterns from `validate_partition_date_field_schema` for required-list and null-only checks (e.g. `types = [raw_type] if isinstance(raw_type, str) else list(raw_type)`; `non_null = [t for t in types if t != "null"]`; empty `non_null` → null-only).
3. **Export** in `loaders/target-gcs/target_gcs/helpers/__init__.py`: add `from .partition_schema import validate_partition_fields_schema` and add `"validate_partition_fields_schema"` to `__all__`.
4. **Run tests** and fix until all pass. Run ruff and mypy from `loaders/target-gcs/`.

---

## Validation Steps

- From `loaders/target-gcs/`: `uv run pytest tests/helpers/test_partition_schema.py -v` — all tests pass.
- `uv run ruff check target_gcs tests` and `uv run ruff format --check target_gcs tests` — no violations.
- `uv run mypy target_gcs` — no type errors.
- No regression: existing tests for `validate_partition_date_field_schema` still pass.

---

## Documentation Updates

- **None** for this task. README and Meltano docs are updated in task 09. In-code docstring: add a concise Google-style docstring to `validate_partition_fields_schema` (Args: stream_name, schema, partition_fields; Returns: None; Raises: ValueError with stream_name, field, reason).
