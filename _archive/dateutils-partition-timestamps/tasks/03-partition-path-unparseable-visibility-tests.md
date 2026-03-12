# Task 03: Partition path unparseable visibility tests (TDD)

## Background

The feature requires that unparseable timestamp strings (e.g. `"not-a-date"`) do not silently fall back to `fallback_date`; the failure must be visible via a warning or an error. Per TDD, tests that encode this behaviour are written before implementation. The existing test `test_partition_path_invalid_value_uses_fallback` currently asserts that an invalid value yields the fallback path with no visibility requirement; it must be updated to match the chosen product behaviour (raise on unparseable, or warning + fallback with a way to assert visibility). Per development_practices and AI_CONTEXT_PATTERNS, black-box tests assert on return values or raised exceptions; prefer an exception test if the implementation raises on unparseable, so the test is a simple `pytest.raises` assertion.

Dependencies: None. Reference: `_features/dateutils-partition-timestamps/plans/master/testing.md`, `implementation.md` Step 2.

## This Task

- **File:** `loaders/target-gcs/tests/helpers/test_partition_path.py`
  - **Update** `test_partition_path_invalid_value_uses_fallback`: Change expectation so that for an unparseable string (e.g. `record={"created_at": "not-a-date"}`) either:
    - **(a)** The test asserts that an exception is raised (e.g. `dateutil.parser.ParserError` or a wrapper such as `ValueError`), using `pytest.raises`; or
    - **(b)** If the product choice is "warning + fallback," the test asserts both that the return value is the fallback path and that visibility is guaranteed (only if the project allows a mechanism for that without asserting on log content; otherwise prefer (a)).
  - **Add** (if not covered by the update) a test that an unparseable string does not result in silent fallback: either assert exception or assert the chosen visibility behaviour. Docstring must state WHAT (unparseable → visible failure) and WHY (no silent fallback).
- **Acceptance criteria:** Tests fail with current implementation (which silently returns fallback); they pass after Task 05 when the helper surfaces the error. Tests are black-box (return value or exception only; no "called_once" or log-line assertions unless project allows).

## Testing Needed

- Updated and/or new tests as above. Each test must be able to fail (e.g. if implementation silently returns fallback, the exception test fails; if implementation raises, the test passes). Valid tests per development_practices.
