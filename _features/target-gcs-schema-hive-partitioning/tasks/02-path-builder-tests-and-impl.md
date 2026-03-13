# Task 02 — Path builder tests and implementation

## Background

Partition paths must be built from stream schema (`x-partition-fields`) and the record. When `x-partition-fields` is missing or empty, the path is the fallback date formatted. This task adds `get_partition_path_from_schema_and_record` in `partition_path.py`. It has no dependency on task 01. Follow TDD: add tests first, then implement.

## This Task

- **File:** `loaders/target-gcs/target_gcs/helpers/partition_path.py`
  - Add `get_partition_path_from_schema_and_record(schema: dict, record: dict, fallback_date: datetime, *, partition_date_format: str = "year=%Y/month=%m/day=%d") -> str`.
  - Read `partition_fields = schema.get("x-partition-fields")`. If missing or empty, return `fallback_date.strftime(partition_date_format)`.
  - Otherwise for each field: get value from record; if date-parseable (schema format "date"/"date-time", or value is date/datetime, or string parseable by dateutil), append one segment YEAR=.../MONTH=.../DAY=... using `partition_date_format`; else append path-safe literal (replace `/` in str(value) with `_`). Join segments with `/` and return.
  - Define default format in this module or import from a shared constant to avoid circular import; see plan.
  - Propagate `ParserError` from dateutil when a string is parsed as date and fails.
- **Interface:** See `plans/master/interfaces.md` for full behaviour and literal sanitization.

## Testing Needed

- **File:** `loaders/target-gcs/tests/helpers/test_partition_path.py`
  - **No x-partition-fields:** schema = {} or no key; any record; fixed fallback_date. Expect return = fallback_date.strftime(partition_date_format).
  - **Empty x-partition-fields:** schema = {"x-partition-fields": []}. Expect same as no key.
  - **Single date field (datetime):** x-partition-fields ["dt"]; properties dt format "date-time"; record dt = datetime(2024,3,11). Expect segment year=2024/month=03/day=11.
  - **Single date field (string ISO):** record dt = "2024-03-11"; format "date". Expect same segment.
  - **Single literal field:** x-partition-fields ["region"]; record region = "eu". Expect "eu".
  - **Two fields enum then date:** x-partition-fields ["region","dt"]; record region="eu", dt=datetime(2024,3,11). Expect "eu/year=2024/month=03/day=11".
  - **Two fields date then enum:** x-partition-fields ["dt","region"]; same record. Expect "year=2024/month=03/day=11/eu".
  - **Literal with slash:** record region = "a/b". Expect path-safe segment (e.g. "a_b").
  - **Unparseable date string:** record dt = "not-a-date"; schema suggests date. Expect ParserError.
- Use fixed fallback_date (e.g. datetime(2024, 1, 15)) and explicit or default partition_date_format for deterministic output. Black-box: assert return path string only.
