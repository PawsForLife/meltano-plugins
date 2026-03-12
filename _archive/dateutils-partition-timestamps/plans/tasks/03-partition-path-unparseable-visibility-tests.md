# Task Plan: 03 — Partition path unparseable visibility tests (TDD)

## Overview

This task updates and adds tests in `test_partition_path.py` so that **unparseable** timestamp strings (e.g. `"not-a-date"`) are required to produce a **visible** failure (warning or error), not a silent fallback to `fallback_date`. It is TDD-only: no production code changes. Tests written here must **fail** with the current implementation (which silently returns the fallback path) and **pass** after Task 05 (Implement partition path dateutil) when the helper surfaces the error.

Scope is limited to the partition-path helper tests; sink-level behaviour for unparseable partition fields is covered in Task 07.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/helpers/test_partition_path.py` | Modify |

### Changes in `test_partition_path.py`

1. **Update** `test_partition_path_invalid_value_uses_fallback`  
   - Current behaviour: asserts that `record={"created_at": "not-a-date"}` yields `FALLBACK_DATE.strftime(DEFAULT_HIVE_FORMAT)` with no visibility requirement.  
   - New behaviour (choose one based on product decision; plan assumes "raise" unless documented otherwise):
   - **Option A (raise on unparseable):** Replace with an exception test: call `get_partition_path_from_record(...)` with `record={"created_at": "not-a-date"}` and assert that `dateutil.parser.ParserError` (or a wrapper such as `ValueError`) is raised, using `pytest.raises`. Remove the assertion on the return value. Docstring: WHAT = unparseable string causes exception; WHY = no silent fallback.
   - **Option B (warning + fallback):** If product chose "warning + fallback," keep asserting that the return value equals the fallback path and add a mechanism to assert visibility **only if** the project allows it without asserting on log content (e.g. a test hook or documented contract). If no black-box mechanism exists, prefer Option A so the test remains black-box.

2. **Add** (if not satisfied by the update above) a dedicated test that an unparseable string does **not** result in silent fallback:
   - Either assert that an exception is raised (same as Option A), or assert the chosen visibility behaviour per Option B.
   - Docstring must state WHAT (unparseable → visible failure) and WHY (no silent fallback). Each test must be able to fail (e.g. with current implementation, an exception test would fail because no exception is raised).

3. **Imports:** Add `import pytest` if using `pytest.raises`. Add `from dateutil.parser import ParserError` (or equivalent) when asserting on `ParserError`; dependency on `python-dateutil` is already added in Task 01.

No other files are created or modified in this task.

---

## Test Strategy

- **TDD:** Tests are written first. They must fail under the current implementation (silent fallback) and pass after Task 05.
- **Black-box:** Assert only on return value or raised exception. Do not assert on "called_once," log lines, or internal call counts (per development_practices and AI_CONTEXT_PATTERNS).
- **Valid tests:** Each test must be able to fail. For example: if the test expects `ParserError` and the implementation still returns the fallback path, the test fails (no exception); after Task 05 raises on unparseable, the test passes.
- **Prefer exception assertion:** If the implementation will raise on unparseable (product decision), use `pytest.raises(ParserError)` (or wrapper) so the test is a simple, black-box exception assertion.

### Test cases (summary)

| Case | Input | Expected (this task) |
|------|--------|----------------------|
| Unparseable string | `record={"created_at": "not-a-date"}`, other args as in existing test | Exception raised (e.g. `ParserError` or `ValueError`), **or** fallback path plus documented visibility (Option B) |

Existing tests (`test_partition_path_valid_iso_date_in_field`, `test_partition_path_valid_iso_datetime_in_field`, `test_partition_path_missing_field_uses_fallback`, `test_partition_path_custom_format`) are **not** modified in this task; they remain as-is.

---

## Implementation Order

1. **Confirm product decision** (if not already in master plan): "raise on unparseable" vs "warning + fallback." If "raise," use Option A; if "warning + fallback" and a black-box visibility mechanism exists, use Option B; otherwise prefer Option A.
2. **Add imports** in `test_partition_path.py`: `pytest` (if using `pytest.raises`), `ParserError` from `dateutil.parser` (requires Task 01 done so `python-dateutil` is installed).
3. **Update** `test_partition_path_invalid_value_uses_fallback` to the chosen behaviour (exception assertion or fallback + visibility).
4. **Add** a separate test for "unparseable → visible failure" if the update in step 3 does not already cover it (e.g. one test for exception, one for a different unparseable value if desired for clarity).
5. **Run tests:** `uv run pytest loaders/target-gcs/tests/helpers/test_partition_path.py -v`. Confirm that the new/updated test(s) **fail** with the current implementation (e.g. expect exception but get return value, or expect no exception but get one after a mistaken change).
6. **Lint/format:** `uv run ruff check .` and `uv run ruff format --check` in `loaders/target-gcs/`.

---

## Validation Steps

- Run `uv run pytest loaders/target-gcs/tests/helpers/test_partition_path.py -v` from `loaders/target-gcs/`: all tests run; the unparseable-visibility test(s) **fail** with current code (no implementation change in this task).
- Run full target-gcs test suite: no regressions in other tests (existing partition_path tests still pass except the one intentionally updated to expect exception or visibility).
- Ruff and (if applicable) mypy pass for the modified file.

---

## Documentation Updates

- **None** for this task. Docstrings in the new/updated tests document WHAT and WHY. AI context and user-facing docs are updated in Task 08.

---

## Dependencies

- **Task 01 (add dateutil dependency):** Must be completed first so `python-dateutil` is in the environment and `from dateutil.parser import ParserError` (and optional use of `dateutil.parser.parse` in tests if needed) works.
- **Task 02, 04:** No dependency; this task can run in parallel with 02 or 04 after 01.
- **Task 05:** Implementation task; the tests from this task will pass once Task 05 is done (raise or surface warning for unparseable).

---

## Acceptance Criteria

- [ ] `test_partition_path_invalid_value_uses_fallback` is updated to assert either (a) an exception is raised for unparseable string, or (b) fallback path plus visibility per product decision, in a black-box way.
- [ ] At least one test encodes "unparseable string → visible failure (no silent fallback)" with a clear WHAT/WHY docstring.
- [ ] All new/updated tests **fail** with the current implementation (no code change in `partition_path.py` in this task).
- [ ] Tests are black-box only (return value or exception; no log or call-count assertions).
- [ ] Existing partition_path tests (valid ISO, missing field, custom format) are unchanged and still pass.
- [ ] Ruff (and project type/lint checks) pass on the modified file.
