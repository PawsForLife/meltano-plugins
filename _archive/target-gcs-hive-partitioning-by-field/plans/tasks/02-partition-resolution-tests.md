# Task Plan: 02-partition-resolution-tests

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Add unit tests for the partition resolution function `get_partition_path_from_record`. Tests define the contract and expected behaviour; implementation follows in task 03.  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/interfaces.md](../master/interfaces.md), [../master/testing.md](../master/testing.md)

---

## 1. Overview

This task adds unit tests for the pure function `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str`. The function will be implemented in task 03; tests are written first (TDD). All tests use a fixed `fallback_date` (e.g. `datetime(2024, 3, 11)`) so outcomes are deterministic. Tests may fail (e.g. import error or assertion failure) until task 03 implements the function. Optionally, a minimal stub in `sinks.py` raises `NotImplementedError` so the test module runs and each test fails in a controlled way.

**Scope:** Test code only; no production behaviour change. Optional stub in `sinks.py` for runnable tests.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/tests/test_sinks.py` | Modify | Add unit tests for `get_partition_path_from_record` (see Test Strategy). Use fixed `fallback_date`; no `datetime.today()` in tests. |
| `loaders/target-gcs/gcs_target/sinks.py` | Modify (optional) | Add minimal stub: `def get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date): raise NotImplementedError`. Enables tests to import and run; they fail until task 03. If no stub, tests will fail on import until task 03. |

**Alternative:** If test file length or separation is preferred, add tests in a new file `loaders/target-gcs/tests/test_sinks_partition.py` that imports `get_partition_path_from_record` from `gcs_target.sinks`. Current `test_sinks.py` is under 300 lines; adding these tests keeps it under 500 (content_length.mdc). Prefer extending `test_sinks.py` unless the team prefers a dedicated partition test module.

**Default format constant:** Tests that assert "default Hive format" use the string `year=%Y/month=%m/day=%d` (per interfaces.md). No need to define a constant in this task; literal in tests is fine.

---

## 3. Test Strategy

**Target:** `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str` (module-level in `sinks.py`; see interfaces.md).

**Import:** `from gcs_target.sinks import get_partition_path_from_record`. Use a fixed `FALLBACK_DATE = datetime(2024, 3, 11)` (or similar) in test scope so all assertions are deterministic.

**Black box:** Assert only on the returned string. No assertions on call counts, logs, or internal behaviour.

| Test | WHAT | WHY |
|------|------|-----|
| **Valid ISO date in field** | Record `{partition_date_field: "2024-03-11"}` with format `year=%Y/month=%m/day=%d` → returns `year=2024/month=03/day=11`. | Core behaviour for partition path from date string. |
| **Valid ISO datetime in field** | Record with `"2024-03-11T12:00:00"` and same format → returns `year=2024/month=03/day=11`. | Datetime is parsed and date part used; common API format. |
| **Fallback format (e.g. %Y-%m-%d)** | Record with `"2024-03-11"` and format that accepts it (e.g. `year=%Y/month=%m/day=%d`) → correct path. | Fallback parsing path works when format matches. |
| **Missing field** | Record without `partition_date_field` key → returns `fallback_date.strftime(partition_date_format)`. | Fallback when field absent; no crash; predictable path. |
| **Invalid value** | Record with non-date string (e.g. `"not-a-date"`) → returns path from `fallback_date.strftime(partition_date_format)`. | Unparseable value uses fallback; robustness. |
| **Custom partition_date_format** | Custom format (e.g. `day=%d/month=%m`) and record with valid date → output matches that format. | Configurable format is applied; flexibility for Hive layouts. |

Each test must have a short docstring stating WHAT is being tested and WHY (per project rules). Tests must be able to fail (e.g. by changing the implementation or input).

---

## 4. Implementation Order

1. **Optional stub in sinks.py**  
   Add at module level (e.g. after imports, before `GCSSink`):  
   `def get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date): raise NotImplementedError`  
   Type hints and docstring optional for stub; task 03 will replace with full implementation.

2. **Test constant and import in test_sinks.py**  
   Define `FALLBACK_DATE = datetime(2024, 3, 11)`. Add import: `from gcs_target.sinks import get_partition_path_from_record` (if not already present, add `datetime` to existing datetime import).

3. **Add six test functions** in `test_sinks.py` (or in `test_sinks_partition.py` if created):
   - `test_partition_path_valid_iso_date_in_field`
   - `test_partition_path_valid_iso_datetime_in_field`
   - `test_partition_path_fallback_format`
   - `test_partition_path_missing_field_uses_fallback`
   - `test_partition_path_invalid_value_uses_fallback`
   - `test_partition_path_custom_format`

4. **Run tests**  
   Expect failures until task 03 implements the function (either `NotImplementedError` from stub or assertion failures).

5. **Lint/format**  
   Run project linter/formatter (e.g. Ruff) on modified files.

---

## 5. Validation Steps

- [ ] All six new tests exist and are documented (WHAT/WHY in docstrings).
- [ ] Tests use only a fixed `fallback_date`; no `datetime.today()` or other non-deterministic input.
- [ ] Tests run without import errors (if stub is added) or are explicitly expected to fail on import until task 03.
- [ ] Existing tests in `test_sinks.py` (and full test suite for `loaders/target-gcs`) still pass — no regression to other tests.
- [ ] Linter/type checker passes for modified files.

---

## 6. Documentation Updates

**This task:** No README, AI context, or sample config changes. Documentation for partition resolution and config is planned in later tasks (e.g. task 08).

**In-code:** Test docstrings suffice for this task; no separate design doc required.
