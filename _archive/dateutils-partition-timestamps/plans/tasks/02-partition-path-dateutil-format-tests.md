# Task Plan: 02-partition-path-dateutil-format-tests

## Overview

This task adds **TDD-only** tests for partition path resolution when the partition date field contains **dateutil-parsable string formats** that the current implementation does not support. The current code in `get_partition_path_from_record` uses only `datetime.fromisoformat` and `strptime("%Y-%m-%d")`; formats such as `"2024/03/11"`, `"11 Mar 2024 12:00:00"`, or `"March 11, 2024"` are not parsed today. These new tests must **fail** with the current implementation and will **pass** after Task 05 (implement partition_path with dateutil). No implementation changes or changes to existing tests are made in this task.

**Scope:** Add 2–3 new test cases in `test_partition_path.py`. Retain all existing tests unchanged.

**Reference:** Master plan `implementation.md` Step 2 (tests for partition_path helper); `testing.md` "Dateutil-parsable formats."

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/helpers/test_partition_path.py` | **Modify** — Add 2–3 new test functions only. Do not remove or alter existing tests. |

**No new files.** No changes to `partition_path.py`, `sinks.py`, or any other module.

---

## Test Strategy

### TDD intent

- New tests are written **first** and must **fail** with the current implementation (no dateutil).
- They will pass once Task 05 replaces parsing in `get_partition_path_from_record` with `dateutil.parser.parse`.

### Tests to add (order)

1. **Dateutil-only format: slash-separated date**
   - Record: `{"created_at": "2024/03/11"}`.
   - Assert: `get_partition_path_from_record(...)` returns `"year=2024/month=03/day=11"` (same as `DEFAULT_HIVE_FORMAT` for 2024-03-11).
   - Rationale: dateutil parses this; current code does not.

2. **Dateutil-only format: RFC-style datetime**
   - Record: `{"created_at": "11 Mar 2024 12:00:00"}` (or equivalent, e.g. `"11 Mar 2024"`).
   - Assert: returned path equals `"year=2024/month=03/day=11"`.
   - Rationale: common API/log format; dateutil parses it; current code does not.

3. **Dateutil-only format: long month name (optional third case)**
   - Record: e.g. `{"created_at": "March 11, 2024"}`.
   - Assert: returned path equals `"year=2024/month=03/day=11"`.
   - Rationale: broadens coverage of dateutil-only formats.

### Test contract (black-box)

- **Assert only on the returned partition path string.** No assertions on internal calls, log output, or call counts (per `development_practices.mdc` and `AI_CONTEXT_PATTERNS.md`).
- Use the same test constants and pattern as existing tests: `FALLBACK_DATE`, `DEFAULT_HIVE_FORMAT`, single partition field `created_at`.
- Each new test must have a **docstring** stating **WHAT** is being tested and **WHY** (per project rules).
- Tests must be **valid**: they must be able to fail (wrong implementation returns a different path or raises; assertion then fails).

### Tests to leave unchanged

- `test_partition_path_valid_iso_date_in_field`
- `test_partition_path_valid_iso_datetime_in_field`
- `test_partition_path_missing_field_uses_fallback`
- `test_partition_path_invalid_value_uses_fallback`
- `test_partition_path_custom_format`

Do **not** in this task: change the invalid-value test (Task 03 covers unparseable visibility) or add custom-format variants for dateutil formats (optional later).

---

## Implementation Order

1. **Open** `loaders/target-gcs/tests/helpers/test_partition_path.py`.
2. **Add** the first new test (slash-separated date `"2024/03/11"`), reusing `FALLBACK_DATE`, `DEFAULT_HIVE_FORMAT`, and `partition_date_field="created_at"`. Docstring: WHAT (dateutil-only format yields correct Hive path) and WHY (ensure broader format support after Task 05).
3. **Add** the second new test (RFC-style e.g. `"11 Mar 2024 12:00:00"` or `"11 Mar 2024"`). Same constants; assert path `"year=2024/month=03/day=11"`. Docstring: WHAT/WHY.
4. **Add** the third new test (e.g. `"March 11, 2024"`) with same pattern and docstring.
5. **Run** the partition path tests and confirm the **new** tests **fail** (current implementation does not parse these formats). Confirm **existing** tests still **pass**.
6. **Run** full target-gcs test suite to ensure no regressions.

---

## Validation Steps

1. **New tests fail with current code**
   From `loaders/target-gcs/`: run
   `uv run pytest tests/helpers/test_partition_path.py -v`
   The new dateutil-format tests must fail (e.g. assertion mismatch or fallback path). This confirms TDD: tests first, implementation in Task 05.

2. **Existing tests still pass**
   All of: `test_partition_path_valid_iso_date_in_field`, `test_partition_path_valid_iso_datetime_in_field`, `test_partition_path_missing_field_uses_fallback`, `test_partition_path_invalid_value_uses_fallback`, `test_partition_path_custom_format` must pass.

3. **Lint and type check**
   From `loaders/target-gcs/`:
   `uv run ruff check tests/helpers/test_partition_path.py`
   `uv run ruff format --check tests/helpers/test_partition_path.py`
   Resolve any issues.

4. **Regression gate**
   Run full plugin test suite: `uv run pytest` from `loaders/target-gcs/`. No failing tests except explicitly marked xfail.

---

## Documentation Updates

- **None** for this task. No code behaviour or public API changes; only new tests are added.
- Task 08 covers documentation and AI context updates for the feature.

---

## Dependencies

- **No prerequisite tasks** for adding these tests. The helper's signature is unchanged; tests call the existing public API.
- **Task 05** will implement dateutil parsing so these new tests pass; Task 02 does not block Task 03 or 04.

---

## Acceptance Criteria (summary)

- [ ] 2–3 new test cases added in `test_partition_path.py` for dateutil-parsable, currently-unsupported string formats.
- [ ] Each new test uses `FALLBACK_DATE`, `DEFAULT_HIVE_FORMAT`, and a single partition field (e.g. `created_at`), and asserts the exact returned partition path string.
- [ ] Each new test has a clear docstring (WHAT is tested, WHY).
- [ ] New tests **fail** with the current implementation; existing tests **pass**.
- [ ] Black-box style: no assertions on logs or internal calls.
- [ ] Ruff and pytest pass; no regressions in the target-gcs test suite.
