# Task 05: Implement partition_path dateutil parsing

## Background

Tasks 01–04 provide the dependency and failing (or updated) tests. This task implements the partition path helper changes so that string timestamps are parsed with dateutil and unparseable/unsupported-timezone cases are surfaced. The public signature of `get_partition_path_from_record` remains unchanged. Behaviour for `None`, `date`/`datetime`, and non-string must be preserved. No new data models or public interfaces.

Dependencies: Task 01 (dependency present), Task 02, Task 03 (and Task 04 if unknown-timezone test was added). Reference: `_features/dateutils-partition-timestamps/plans/master/implementation.md` Step 3, `interfaces.md`, `architecture.md`.

## This Task

- **File:** `loaders/target-gcs/target_gcs/helpers/partition_path.py`
  1. **Imports:** Add `from dateutil import parser as dateutil_parser` and use `dateutil_parser.ParserError`; if handling warnings, `dateutil_parser.UnknownTimezoneWarning`.
  2. **Preserve:** Logic for `value is None`, `isinstance(value, (datetime, date))`, and `not isinstance(value, str)` unchanged; return fallback or strftime as today.
  3. **Replace** the block that uses `fromisoformat` and `strptime("%Y-%m-%d")` with:
     - Try: `parsed = dateutil_parser.parse(value)` (no `tzinfos`).
     - On success: `return parsed.strftime(partition_date_format)`.
     - Except `ParserError`: log warning (include field name and value if safe); then either re-raise or return `fallback_date.strftime(partition_date_format)` per product decision.
     - For `UnknownTimezoneWarning` (optional): wrap the parse call in `warnings.catch_warnings(record=True)`, filter for `UnknownTimezoneWarning`; if any were recorded, log warning and either treat as error (raise or return fallback after log) or use the naive datetime for strftime, per product decision.
  4. **Optional:** Extract an internal helper `_parse_timestamp_for_partition(value: str) -> datetime` that calls `dateutil_parser.parse(value)` and raises `ParserError`; use it inside `get_partition_path_from_record`. Do not export it in `__all__`.
  5. **Docstring:** Update the docstring to state that string values are parsed with dateutil; that unparseable (`ParserError`) or unsupported timezone (`UnknownTimezoneWarning`) are surfaced via warning or error; and optionally that fallback path is returned after logging. Keep Args, Returns, and Callers note consistent with existing style.
  6. **Comment:** Short comment above the dateutil parse block: use dateutil for flexible format support; do not pass `tzinfos`.
- **Acceptance criteria:** All tests in `tests/helpers/test_partition_path.py` (existing + Task 02, 03, 04) pass. No new config or timezone list. Signature of `get_partition_path_from_record` unchanged.

## Testing Needed

- No new tests in this task; tests were added in Tasks 02, 03, 04. Run the full target-gcs test suite and fix any regressions. Existing tests for valid ISO date/datetime, missing field, custom format must still pass. Updated invalid-value and new dateutil-format and optional unknown-timezone tests must pass.
