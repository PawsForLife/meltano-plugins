# Task Plan — 02: Path builder tests and implementation

## Overview

This task adds the schema-and-record–driven partition path builder `get_partition_path_from_schema_and_record` in `partition_path.py` and its tests. It has no dependency on task 01 (validator). When `x-partition-fields` is missing or empty, the path is the fallback date formatted; otherwise the path is built from field values in order (date-parseable → one Hive date segment; else path-safe literal). TDD: tests first, then implementation.

**Scope:** `loaders/target-gcs/target_gcs/helpers/partition_path.py` and `loaders/target-gcs/tests/helpers/test_partition_path.py` only. No sink, config, or exports changes in this task.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/helpers/test_partition_path.py` | Add tests for `get_partition_path_from_schema_and_record` (see Test Strategy). Keep existing tests for `get_partition_path_from_record` unchanged. |
| `loaders/target-gcs/target_gcs/helpers/partition_path.py` | Add constant `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"`; add `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`; implement fallback, date vs literal, segment building, literal sanitization; propagate `ParserError` from dateutil. Do not remove or change `get_partition_path_from_record`. |

---

## Test Strategy

**File:** `loaders/target-gcs/tests/helpers/test_partition_path.py`

Write these tests **first** (TDD). Use fixed `fallback_date` (e.g. `datetime(2024, 1, 15)`) and default or explicit `partition_date_format` for deterministic output. Black-box: assert only the returned path string or raised exception. Import `get_partition_path_from_schema_and_record` from `target_gcs.helpers.partition_path` (or from `target_gcs.helpers` once task 03 exports it; for this task, import from `partition_path` module directly to avoid depending on task 03).

| # | Test | What | Expected |
|---|------|------|----------|
| 1 | No x-partition-fields | schema = {} or no key; any record; fixed fallback_date | Return = `fallback_date.strftime(partition_date_format)` |
| 2 | Empty x-partition-fields | schema = `{"x-partition-fields": []}` | Same as no key (fallback path) |
| 3 | Single date field (datetime) | x-partition-fields `["dt"]`; properties dt format `"date-time"`; record dt = `datetime(2024,3,11)` | One segment `year=2024/month=03/day=11` |
| 4 | Single date field (string ISO) | record dt = `"2024-03-11"`; format `"date"` | Same segment as above |
| 5 | Single literal field | x-partition-fields `["region"]`; record region = `"eu"`; no date format on property | Return `"eu"` |
| 6 | Two fields enum then date | x-partition-fields `["region","dt"]`; record region=`"eu"`, dt=`datetime(2024,3,11)` | Return `"eu/year=2024/month=03/day=11"` |
| 7 | Two fields date then enum | x-partition-fields `["dt","region"]`; same record | Return `"year=2024/month=03/day=11/eu"` |
| 8 | Literal with slash | record region = `"a/b"` | Path-safe segment (e.g. `"a_b"`); full path = that segment only or combined with others |
| 9 | Unparseable date string | record dt = `"not-a-date"`; schema suggests date (format `"date"` or `"date-time"`) | `pytest.raises(ParserError)` (from dateutil.parser) |

**Test data:** Reuse a constant for default format (e.g. `DEFAULT_HIVE_FORMAT` already in test file). Schema fixtures: minimal `properties` and optional `format` per field; include `required` only if a test cares about presence (path builder reads record only; validation of required is task 01).

---

## Implementation Order

1. **Add tests** in `test_partition_path.py` for `get_partition_path_from_schema_and_record` as in Test Strategy (all 9 cases). Run pytest; expect failures (function not yet implemented or import path).
2. **Add constant** in `partition_path.py`: `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"`.
3. **Implement** `get_partition_path_from_schema_and_record` in `partition_path.py`:
   - Signature: `def get_partition_path_from_schema_and_record(schema: dict, record: dict, fallback_date: datetime, *, partition_date_format: str = DEFAULT_PARTITION_DATE_FORMAT) -> str`.
   - Read `partition_fields = schema.get("x-partition-fields")`. If missing or empty (or not a non-empty list), return `fallback_date.strftime(partition_date_format)`.
   - For each field in partition_fields: get value from record; determine date vs literal (see interfaces.md): property `format` in `("date", "date-time")` → date; else value is `datetime` or `date` → date; else value is str and dateutil.parser.parse(value) succeeds → date; else → literal. Date: append one segment via strftime with partition_date_format (reuse same pattern as `get_partition_path_from_record`: value.strftime or parsed.strftime). Literal: append path-safe segment: `str(value).replace("/", "_")`. Join segments with `/` and return.
   - When treating as date and value is str, call dateutil.parser.parse(value); do not catch ParserError (propagate to caller).
   - Docstring: document args, return, and that ParserError is raised for unparseable date strings.
4. **Run tests** until all new tests pass. Fix any test or implementation bug; ensure no regression in existing `get_partition_path_from_record` tests.
5. **Lint and type-check:** `ruff check .`, `ruff format --check`, `mypy target_gcs` from `loaders/target-gcs/`.

---

## Validation Steps

- From `loaders/target-gcs/`: `uv run pytest tests/helpers/test_partition_path.py -v` — all tests pass.
- From `loaders/target-gcs/`: `uv run ruff check target_gcs/ tests/` and `uv run ruff format --check .` — no violations.
- From `loaders/target-gcs/`: `uv run mypy target_gcs` — no errors.
- No changes in this task to `sinks.py`, `target.py`, `helpers/__init__.py`, or any file outside `partition_path.py` and `test_partition_path.py`.

---

## Documentation Updates

- **In-code:** Add a concise Google-style docstring for `get_partition_path_from_schema_and_record` (args, return, ParserError, and brief behaviour: fallback when no x-partition-fields; date segment vs path-safe literal; literal slash replaced).
- **No README or AI context changes in this task** — those are covered in later tasks (e.g. task 09, or when exports are added in task 03).
