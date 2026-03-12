# Task Plan: 05-implement-partition-path-dateutil

## Overview

This task implements the partition path helper changes in `get_partition_path_from_record` so that string timestamps are parsed with **python-dateutil** and unparseable or unsupported-timezone cases are surfaced. The public signature of `get_partition_path_from_record` remains unchanged. Behaviour for `None`, `date`/`datetime`, and non-string must be preserved. No new data models or public interfaces. Tests were added in Tasks 02, 03, and optionally 04; this task implements the code so those tests pass and all existing tests continue to pass.

**Scope:** Single file — `loaders/target-gcs/target_gcs/helpers/partition_path.py`. No new tests in this task; run full target-gcs test suite and fix regressions.

**Reference:** Master plan `implementation.md` Step 3; `interfaces.md`; `architecture.md`; task doc `tasks/05-implement-partition-path-dateutil.md`.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/helpers/partition_path.py` | **Modify** — Add dateutil imports; preserve None/date/datetime/non-string branches; replace fromisoformat/strptime block with dateutil parse and ParserError (and optionally UnknownTimezoneWarning) handling; optional internal helper; update docstring and add short comment. |

**No new files.** No changes to `sinks.py`, `__init__.py`, or test files in this task (sink exception handling is Task 06; doc/AI_CONTEXT is Task 08).

---

## Test Strategy

- **No new tests** in this task. Tests for dateutil formats, unparseable visibility, and (optionally) unknown timezone were added in Tasks 02, 03, and 04.
- **TDD alignment:** Implement until all tests in `tests/helpers/test_partition_path.py` pass, including the tests added in 02–04. The exact behaviour for `ParserError` (raise vs warning + fallback) and for `UnknownTimezoneWarning` (if any) is defined by those tests; implement to satisfy them.
- **Regression:** Run the full target-gcs test suite. Existing tests for valid ISO date/datetime, missing field, custom format, and invalid value (as updated in Task 03) must pass. Fix any regressions before considering the task complete.
- **Black-box:** Do not add tests that assert on log lines or call counts; the implementer only runs existing tests and fixes code until they pass.

---

## Implementation Order

1. **Imports**  
   Add `from dateutil import parser as dateutil_parser`. Use `dateutil_parser.ParserError`; if handling `UnknownTimezoneWarning` (per Task 04), also use `dateutil_parser.UnknownTimezoneWarning`. Add `import warnings` if using `warnings.catch_warnings` for unknown timezone.

2. **Preserve existing branches**  
   Keep unchanged: `value is None` → return `fallback_date.strftime(partition_date_format)`; `isinstance(value, (datetime, date))` → return `value.strftime(partition_date_format)`; `not isinstance(value, str)` → return `fallback_date.strftime(partition_date_format)`.

3. **Replace string-parsing block**  
   Remove the existing `try/except` block that uses `datetime.fromisoformat(value)` and `datetime.strptime(value, "%Y-%m-%d")`. Replace with:
   - A short comment above the block: use dateutil for flexible format support; do not pass `tzinfos`.
   - `try: parsed = dateutil_parser.parse(value)` (no `tzinfos` argument).
   - On success: `return parsed.strftime(partition_date_format)`.
   - `except ParserError`: log warning (include partition_date_field and value if safe); then either re-raise or return `fallback_date.strftime(partition_date_format)` per the behaviour asserted in Task 03 tests (raise vs warning + fallback).
   - For `UnknownTimezoneWarning` (optional, only if Task 04 added a test): wrap the parse call in `warnings.catch_warnings(record=True)`, filter for `UnknownTimezoneWarning`; if any were recorded, log warning and either treat as error (raise or return fallback after log) or use the naive datetime for strftime, per Task 04 test expectations.

4. **Optional internal helper**  
   If extracting for clarity: define `_parse_timestamp_for_partition(value: str) -> datetime` that calls `dateutil_parser.parse(value)` and lets `ParserError` propagate; use it inside `get_partition_path_from_record`. Do not add it to `__all__` in `helpers/__init__.py` (it is internal). If not used, keep logic inline.

5. **Docstring and comment**  
   Update the docstring of `get_partition_path_from_record` to state that string values are parsed with dateutil; that unparseable (`ParserError`) or unsupported timezone (`UnknownTimezoneWarning`) are surfaced via warning or error; and optionally that the fallback path is returned after logging. Keep Args, Returns, and the note about callers using `DEFAULT_PARTITION_DATE_FORMAT` consistent with existing style. Ensure the short comment above the dateutil parse block is in place.

---

## Validation Steps

1. From `loaders/target-gcs`, activate the project venv (e.g. `source .venv/bin/activate`) and ensure `python-dateutil` is installed (Task 01).
2. Run: `pytest tests/ -v` (or the project’s test command from `pyproject.toml`). All tests must pass.
3. Confirm in particular:
   - `tests/helpers/test_partition_path.py`: all tests pass (existing + Task 02 dateutil-format tests + Task 03 unparseable visibility + Task 04 unknown-timezone if present).
   - No regressions in `tests/test_partition_key_generation.py` or other target-gcs tests.
4. Resolve any linter/type issues in `partition_path.py` (e.g. Ruff, MyPy per project config).

---

## Documentation Updates

- **In this task:** Update only the **docstring** and **inline comment** in `loaders/target-gcs/target_gcs/helpers/partition_path.py` as described in Implementation Order step 5. No changes to `docs/AI_CONTEXT/` or README in this task (Task 08).

---

## Dependencies and Prerequisites

- **Task 01** must be complete: `python-dateutil` is declared in `loaders/target-gcs/pyproject.toml` and the environment has it installed.
- **Tasks 02 and 03** must be complete: tests for dateutil formats and unparseable visibility exist; implement to satisfy them.
- **Task 04** (optional): If the unknown-timezone test was added, implement UnknownTimezoneWarning handling so that test passes; otherwise omit or leave as xfail.

---

## Acceptance Criteria (Summary)

- All tests in `tests/helpers/test_partition_path.py` (existing + Task 02, 03, 04) pass.
- Signature of `get_partition_path_from_record` unchanged.
- Behaviour for `None`, `date`/`datetime`, and non-string unchanged.
- String values parsed with `dateutil.parser.parse(value)` (no `tzinfos`); on success return `parsed.strftime(partition_date_format)`.
- On `ParserError` (and optionally `UnknownTimezoneWarning`): behaviour matches tests (raise or warning + fallback as decided in 02/03/04).
- No new config or timezone list. Full target-gcs test suite passes; no regressions.
