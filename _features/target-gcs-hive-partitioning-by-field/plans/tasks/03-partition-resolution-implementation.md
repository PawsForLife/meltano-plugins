# Task Plan: 03-partition-resolution-implementation

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Implement the partition resolution function in `sinks.py` so all tests added in task 02 pass.  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/interfaces.md](../master/interfaces.md), [../master/testing.md](../master/testing.md)

---

## 1. Overview

This task implements the pure function `get_partition_path_from_record` and a default Hive partition format constant in `loaders/target-gcs/gcs_target/sinks.py`. Behaviour is already specified by task 02 tests: parse the record’s date field (ISO and one fallback format), use injectable `fallback_date` when the field is missing or unparseable, and return a formatted partition path string. No new tests are added; success is defined as all partition-resolution tests from task 02 passing and no new external dependencies (stdlib only).

**Scope:** Implementation only in `sinks.py`. No changes to target config, key building, or `process_record` (those are later tasks).

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | Modify | Add module-level constant `DEFAULT_PARTITION_DATE_FORMAT` (e.g. `"year=%Y/month=%m/day=%d"`). Add module-level function `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str` with parsing logic and Google-style docstring. |

No new files. No changes to `target.py`, tests, or other modules.

---

## 3. Test Strategy

- **No new tests in this task.** All behaviour is covered by tests added in task 02.
- **Validation:** Run the full test suite for `loaders/target-gcs` (or at least `tests/test_sinks.py`). All partition-resolution tests must pass.
- **Edge case:** If during implementation an edge case is found that raises (e.g. invalid format string passed to `strftime`), add a test that documents the expected exception per [../master/testing.md](../master/testing.md) (Exception tests) and then implement so the code either satisfies that contract or avoids the exception (e.g. by validating the format or catching and falling back).

---

## 4. Implementation Order

1. **Add default format constant**  
   At module level in `sinks.py`, define e.g. `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"` so callers (in later tasks) can use it when `partition_date_format` is omitted. Document in the function docstring that this is the default Hive-style format.

2. **Implement `get_partition_path_from_record`**  
   - **Signature:** `def get_partition_path_from_record(record: dict, partition_date_field: str, partition_date_format: str, fallback_date: datetime) -> str`  
   - **Logic:**  
     - Read `value = record.get(partition_date_field)`.  
     - If `value` is missing (`None` or key absent): return `fallback_date.strftime(partition_date_format)`.  
     - If `value` is already `datetime` or `date`: use it (normalize to date if needed for formatting).  
     - Else treat as string: try `datetime.fromisoformat(value)`; on failure try `datetime.strptime(value, "%Y-%m-%d")`.  
     - If parsing fails or value is invalid: return `fallback_date.strftime(partition_date_format)`.  
     - Return the parsed (or fallback) date formatted with `partition_date_format` via `strftime`.  
   - Use only stdlib: `datetime` (and `date` if needed). No exceptions for bad data; fallback only.

3. **Add docstring**  
   Google-style: brief summary; Args for `record`, `partition_date_field`, `partition_date_format`, `fallback_date`; Returns (partition path string); note that missing or unparseable field uses `fallback_date` and that the default format used by callers is Hive-style (reference the constant).

4. **Run tests**  
   Execute the project test suite (e.g. `pytest loaders/target-gcs/tests/` or `uv run pytest ...` from repo root with venv active). Fix any failing partition-resolution tests until all pass.

---

## 5. Validation Steps

- All tests in `loaders/target-gcs/tests/test_sinks.py` pass, including those for `get_partition_path_from_record` from task 02 (valid ISO date, valid ISO datetime, fallback format, missing field, invalid value, custom partition_date_format).
- No new third-party imports in `sinks.py`; only stdlib (`datetime` / `date`) used for parsing and formatting.
- Function is callable as a module-level symbol (e.g. `from gcs_target.sinks import get_partition_path_from_record`) so tests can import it directly if written that way, or tests may import the module and call `sinks.get_partition_path_from_record`.

---

## 6. Documentation Updates

- **Code:** Add the Google-style docstring to `get_partition_path_from_record` only. No README or AI context changes in this task (documentation is task 08; AI context task 09).
