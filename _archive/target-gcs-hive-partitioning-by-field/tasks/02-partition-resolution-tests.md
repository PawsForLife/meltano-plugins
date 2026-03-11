# Background

Partition resolution is a pure function: given a record, field name, format string, and fallback datetime, it returns a partition path string. The behaviour must be fully testable with no non-determinism (fallback_date is injected). This task adds unit tests that define the contract and behaviour; the implementation follows in task 03.

**Dependencies:** Task 01 (config schema) is not strictly required for tests that call the function directly with explicit args; recommended after 01 so config and code stay in sync.

**Plan reference:** `plans/master/interfaces.md` (Partition resolution), `plans/master/testing.md` (Unit tests: partition resolution).

---

# This Task

- **File:** `loaders/target-gcs/tests/test_sinks.py` (or a dedicated `test_sinks_partition.py` if preferred to keep file size manageable).
- Add unit tests for the function `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str` (module-level in `sinks.py` or private on GCSSink; callable must accept `fallback_date` as argument).
- Use a fixed `fallback_date` (e.g. `datetime(2024, 3, 11)`) in all tests so outcomes are deterministic. Do not rely on `datetime.today()` in tests.
- **Acceptance criteria:** All of the following test cases exist and are documented with WHAT/WHY; they may fail until task 03 implements the function.

---

# Testing Needed

- **Valid ISO date in field:** Record `{partition_date_field: "2024-03-11"}` with default Hive format → returns `year=2024/month=03/day=11`. **WHAT:** Parsed date is formatted correctly. **WHY:** Core behaviour for partition path.
- **Valid ISO datetime in field:** Record with `"2024-03-11T12:00:00"` → partition path uses date part in Hive format. **WHAT:** Datetime is parsed and formatted. **WHY:** Common API format.
- **Fallback format (e.g. %Y-%m-%d):** Record with `"2024-03-11"` and format that accepts it → correct path. **WHAT:** Fallback parsing works. **WHY:** Support non-ISO strings.
- **Missing field:** Record without the key → returns `fallback_date.strftime(partition_date_format)`. **WHAT:** Fallback when field absent. **WHY:** No crash; predictable path.
- **Invalid value:** Record with non-date string (e.g. `"not-a-date"`) → returns fallback path. **WHAT:** Unparseable value uses fallback. **WHY:** Robustness.
- **Custom partition_date_format:** Custom format (e.g. `day=%d/month=%m`) → output matches. **WHAT:** Configurable format is applied. **WHY:** Flexibility for different Hive layouts.

Implement the tests first (TDD); they will fail until `get_partition_path_from_record` is implemented in task 03.
