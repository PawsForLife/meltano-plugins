# Background

The partition resolution function is used by the sink to derive the partition path string for each record. It must be pure, use only stdlib date parsing, and accept an injectable fallback_date for tests. Tests are already in place from task 02.

**Dependencies:** Task 02 (partition resolution tests). Task 01 (config schema) is recommended so default format constant aligns with schema docs.

**Plan reference:** `plans/master/interfaces.md` (Partition resolution), `plans/master/implementation.md` (get_partition_path_from_record in sinks.py).

---

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- Add function `get_partition_path_from_record(record: dict, partition_date_field: str, partition_date_format: str, fallback_date: datetime) -> str`.
- **Behaviour:** Read `record.get(partition_date_field)`. Parse as date/datetime (e.g. `datetime.fromisoformat`; one or two fallback formats such as `%Y-%m-%d`). If missing or unparseable, return `fallback_date.strftime(partition_date_format)`. Return formatted string; no exception for bad data.
- Define a default Hive format constant (e.g. `year=%Y/month=%m/day=%d`) for use when `partition_date_format` is omitted by callers.
- **Placement:** Module-level in `sinks.py` (or private method on GCSSink that delegates to a module-level function so fallback_date remains injectable).
- Add a short Google-style docstring: inputs (record, field name, format, fallback_date), output (partition path string), fallback behaviour.
- **Acceptance criteria:** All tests from task 02 pass; no new external dependencies (stdlib only).

---

# Testing Needed

- No new tests in this task; verify all tests added in task 02 pass. If any edge case (e.g. invalid format string) is found to raise, add a test documenting the expected exception per `plans/master/testing.md` (Exception tests).
