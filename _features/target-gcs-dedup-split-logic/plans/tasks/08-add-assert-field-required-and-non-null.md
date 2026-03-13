# Task Plan: 08-add-assert-field-required-and-non-null

## Overview

This task extracts the shared “field in properties, in required, and non-null type” logic from `validate_partition_fields_schema` and `validate_partition_date_field_schema` in `partition_schema.py` into a module-private helper `_assert_field_required_and_non_null_type`, then refactors both public validators to call it. Behaviour and exception messages remain consistent; no change to public API or to `helpers/__init__.py` exports.

**Feature context:** Part of target-gcs-dedup-split-logic (unify duplicated validation). See [master implementation.md](../master/implementation.md) step 8 and [interfaces.md](../master/interfaces.md) (`_assert_field_required_and_non_null_type`).

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/helpers/partition_schema.py` | Add `_assert_field_required_and_non_null_type`; refactor both public validators to call it; add Google-style docstring for the helper. |

**No new files.** No changes to `helpers/__init__.py` (helper is not exported).

### partition_schema.py — Specific changes

1. **Add `_assert_field_required_and_non_null_type`**
   - Signature: `def _assert_field_required_and_non_null_type(stream_name: str, field_name: str, schema: dict, *, field_label: str = "partition field", no_type_reason: str = "has no type (null-only or missing).", null_only_reason: str = "is null-only.") -> None`
   - Optional kwargs preserve exact message text: `validate_partition_fields_schema` uses defaults; `validate_partition_date_field_schema` passes `field_label="partition_date_field"`, `no_type_reason="has non–date-parseable type."`, `null_only_reason="is null-only and cannot be parsed to a date."`.
   - Validation order (raise ValueError with messages below):
     1. If `schema.get("required")` is not a list → `"Stream '{stream_name}': schema 'required' must be a list."`
     2. If `field_name` not in `schema.get("properties") or {}` → `"Stream '{stream_name}': {field_label} '{field_name}' is not in schema."`
     3. If `field_name` not in required → `"Stream '{stream_name}': {field_label} '{field_name}' must be required for the stream."`
     4. Get `prop_schema = properties[field_name]`, `raw_type = prop_schema.get("type")`; if `raw_type is None` → `"Stream '{stream_name}': {field_label} '{field_name}' {no_type_reason}"` (reasons include trailing period).
     5. `types = [raw_type] if isinstance(raw_type, str) else list(raw_type)`; `non_null = [t for t in types if t != "null"]`; if not non_null → `"Stream '{stream_name}': {field_label} '{field_name}' {null_only_reason}"`
   - Docstring: Google-style; purpose (assert field is in properties, in required, and has at least one non-null type); Args (stream_name, field_name, schema, field_label, no_type_reason, null_only_reason); Raises (ValueError with messages above).

2. **Refactor `validate_partition_fields_schema`**
   - After resolving `properties` and `required`, for each `field` in `partition_fields`: call `_assert_field_required_and_non_null_type(stream_name, field, schema)` (default labels). Remove the duplicated block that checks properties, required, raw_type, types, non_null.

3. **Refactor `validate_partition_date_field_schema`**
   - Call `_assert_field_required_and_non_null_type(stream_name, field_name, schema, field_label="partition_date_field", no_type_reason="has non–date-parseable type.", null_only_reason="is null-only and cannot be parsed to a date.")`. Then re-read `prop_schema`, `raw_type`, resolve `types` and `non_null` from the property (same logic as today) and run the existing date-parseable loop; raise `"Stream '...': partition_date_field '...' has non–date-parseable type."` if no type is date-parseable.

## Test Strategy

- **Regression:** Run existing `loaders/target-gcs/tests/helpers/test_partition_schema.py` and any sink-init tests in `test_sinks.py` that exercise partition schema validation. All must pass without change.
- **TDD:** Existing tests already cover: required not a list; field not in properties; field not in required; no type (missing); null-only (single and list); and success cases. If any branch of the helper is not covered (e.g. “required is not a list” is covered by both validators’ tests), no new test is required. If a branch is missing, add a test that expects `ValueError` with `pytest.raises(ValueError)` and asserts on message content (stream name, field name, or reason substring). Black-box: assert on raised exception and message only; do not assert on call counts.
- **Message consistency:** After refactor, run tests and confirm no test expects the old message text to change; if the helper is implemented with `field_label` and optional `no_type_reason`/`null_only_reason`, existing tests should pass as-is.

## Implementation Order

1. Implement `_assert_field_required_and_non_null_type(stream_name, field_name, schema, *, field_label="partition field", no_type_reason="has no type (null-only or missing).", null_only_reason="is null-only.")` with the five checks in order; reuse exact message format from current validators. Add Google-style docstring (purpose, Args, Raises).
2. Refactor `validate_partition_fields_schema`: for each partition field, call `_assert_field_required_and_non_null_type(stream_name, field, schema)`; remove the in-loop checks for properties, required, type, non_null.
3. Refactor `validate_partition_date_field_schema`: call `_assert_field_required_and_non_null_type(stream_name, field_name, schema, field_label="partition_date_field", no_type_reason="has non–date-parseable type.", null_only_reason="is null-only and cannot be parsed to a date.")`; then re-resolve `prop_schema`, `raw_type`, `types`, `non_null` and run the existing date-parseable loop; raise “has non–date-parseable type” if not date-parseable.
4. Run `uv run pytest loaders/target-gcs/tests/helpers/test_partition_schema.py loaders/target-gcs/tests/test_sinks.py -k partition` (or full suite) to confirm all pass.

## Validation Steps

1. **Tests:** From `loaders/target-gcs/`, run `uv run pytest`. All tests must pass.
2. **Linting/formatting:** Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs`. Fix any issues in `partition_schema.py`.
3. **Type check:** Run `uv run mypy target_gcs`; no new errors in `partition_schema.py`.
4. **Behaviour:** Exception types and message text from both validators must remain the same as before refactor (verified by existing tests).

## Documentation Updates

- **Code:** Add Google-style docstring for `_assert_field_required_and_non_null_type` only. Public validator docstrings remain; update only if they now “delegate” the common checks to the helper (optional one-line note).
- **AI context / README:** No update required for this task; task 09 may refresh component docs.
