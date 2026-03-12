# Task Plan: 04 — Partition path unknown-timezone tests (TDD, optional)

## Overview

This task adds a **single optional test** for the partition path helper: when the implementation (Task 05) detects and surfaces `UnknownTimezoneWarning` (dateutil cannot resolve a timezone name in the string), the test asserts that the behaviour is visible (warning or error) and not silent fallback. The task is **optional**: if the team defers or skips UnknownTimezoneWarning handling in Task 05, the implementer either skips adding the test or adds it marked `@pytest.mark.xfail` with a clear reason. No production code is written in this task; it is test-only (TDD).

**Scope:** One test in `test_partition_path.py`. No changes to `partition_path.py`, sinks, or other files.

**Dependencies:** Task 01 (dateutil dependency) and Task 02 (dateutil format tests) should be done so the test file and imports are consistent. Task 03 (unparseable visibility) is independent. This task does not block Task 05; Task 05 may or may not implement UnknownTimezoneWarning handling.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/helpers/test_partition_path.py` | **Modify.** Add one test (or one xfail test) for unknown-timezone visibility. No other changes. |

**No files created.** No changes to `target_gcs/helpers/partition_path.py`, `sinks.py`, or docs in this task.

---

## Test Strategy

### TDD approach

- **Test first:** Add the unknown-timezone test (or xfail placeholder) before Task 05 implements the behaviour. If Task 05 implements UnknownTimezoneWarning handling, the test will start failing until the implementation is added; then it passes. If Task 05 does not implement it, the test is either omitted or marked xfail so the suite stays green.
- **Black-box:** Assert on observable behaviour only: either (1) an exception is raised when a string that triggers `UnknownTimezoneWarning` is passed, or (2) a warning is emitted (e.g. via `warnings.catch_warnings(record=True)`) and the test asserts that `UnknownTimezoneWarning` was in the list — no assertion on log message content. Prefer exception assertion if the product choice is “raise”; use recorded warnings if the choice is “warning + fallback.”
- **Valid test:** The test must be able to fail. Use a concrete input (e.g. a timestamp string with a timezone name that dateutil does not resolve) and a concrete expected outcome (exception type or presence of `UnknownTimezoneWarning` in recorded warnings).

### Test to add

**Name (suggested):** `test_partition_path_unknown_timezone_surfaces_visibility` (or `test_partition_path_unsupported_timezone_warning_or_error`).

**Input:** A string that triggers `UnknownTimezoneWarning` from dateutil. Example: a datetime string with a timezone abbreviation or name that dateutil does not resolve (e.g. `"2024-03-11 12:00:00 FOO"` or a known-unresolved tz name per dateutil version). The exact string can be chosen during implementation; it must be one that causes `dateutil.parser.parse(...)` to emit `UnknownTimezoneWarning` when warnings are not suppressed.

**Assertion (branch by product decision):**

- **If “raise on unknown timezone”:**  
  `get_partition_path_from_record(...)` is called with the above record; use `pytest.raises(ExpectedException)` (e.g. `ValueError` or a documented wrapper). Assert no silent return of fallback path.
- **If “warning + fallback”:**  
  Use `warnings.catch_warnings(record=True)` and filter for `UnknownTimezoneWarning`; call `get_partition_path_from_record(...)`; assert that at least one `UnknownTimezoneWarning` was recorded (visibility). Optionally assert return value is fallback path if that is the specified behaviour.

**Docstring:** State WHAT (unsupported timezone in string → visible warning or error) and WHY (no silent fallback for unsupported timezone). Follow existing style in `test_partition_path.py`.

**If UnknownTimezoneWarning handling is deferred:**

- **Option A:** Do not add the test; document in the task that the test was skipped and will be added when the feature is implemented.
- **Option B:** Add the test and mark it `@pytest.mark.xfail(reason="UnknownTimezoneWarning handling not yet implemented")` so it is executed but expected to fail until Task 05 (or a later task) implements it.

---

## Implementation Order

1. **Decide product stance** (or assume “implement” for the plan): Confirm whether Task 05 will detect and surface `UnknownTimezoneWarning`. If unknown, implement Option B (add test with xfail) so the test exists and can be switched to pass when the feature is added.
2. **Choose trigger string:** Pick a timestamp string that triggers `UnknownTimezoneWarning` under the project’s dateutil version (e.g. in a small script or existing test: `dateutil.parser.parse("2024-03-11 12:00:00 FOO")` with `warnings.simplefilter("always")` and confirm the warning is emitted). Use that string in the test.
3. **Add test in `test_partition_path.py`:**
   - Use the same constants as existing tests (`FALLBACK_DATE`, `DEFAULT_HIVE_FORMAT`).
   - Call `get_partition_path_from_record(record={partition_date_field: trigger_string}, partition_date_field=..., partition_date_format=..., fallback_date=FALLBACK_DATE)`.
   - Assert exception (with `pytest.raises`) or recorded `UnknownTimezoneWarning`, per strategy above.
   - Add a clear WHAT/WHY docstring.
4. **If deferred:** Either skip adding the test and document, or add it with `@pytest.mark.xfail(reason="...")`.
5. **Run tests:** From `loaders/target-gcs`, run `uv run pytest tests/helpers/test_partition_path.py -v`. If the test is xfail, expect it to show as xfailed; if the feature is implemented, expect it to pass.

---

## Validation Steps

- [ ] Exactly one new test exists in `test_partition_path.py` for unknown-timezone visibility (or an xfail placeholder), with a clear docstring (WHAT/WHY).
- [ ] Test uses black-box assertions only (exception or recorded warning; no log message content).
- [ ] Test is able to fail when the behaviour is wrong (e.g. if implementation silently returns fallback without warning/raise, the test fails).
- [ ] From `loaders/target-gcs`: `uv run pytest tests/helpers/test_partition_path.py` passes (new test passes when feature is implemented, or is xfailed when deferred).
- [ ] Full target-gcs test suite: `uv run pytest` passes (no regressions).
- [ ] Ruff and mypy from plugin root pass (no new issues).

---

## Documentation Updates

**None required for this task.** No changes to `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` or to docstrings in `partition_path.py` in Task 04. Task 08 covers documentation; if the unknown-timezone behaviour is documented there, it can reference this test as the acceptance test for unsupported timezone visibility.

---

## Reference

- Task doc: `_features/dateutils-partition-timestamps/tasks/04-partition-path-unknown-timezone-tests.md`
- Master plan: `_features/dateutils-partition-timestamps/plans/master/` — `testing.md` (optional UnknownTimezoneWarning test), `implementation.md` (Step 2 optional add).
- Interfaces: `interfaces.md` — contract for `get_partition_path_from_record` (surfaces unparseable/unsupported-timezone via log and/or raise).
