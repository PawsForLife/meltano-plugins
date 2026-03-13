# Task 08 — Sink and key generation tests

## Background

Sink behaviour and key generation must be validated with black-box tests: assert keys/paths and observable behaviour, not call counts or logs. Depends on task 07 (dispatch and record processing in place).

## This Task

- **File:** `loaders/target-gcs/tests/test_sinks.py`
  - **hive_partitioned false:** Build sink with hive_partitioned false. process_record(record). Assert key does not contain partition segments from record (flat or existing behaviour).
  - **hive_partitioned true, no x-partition-fields:** Schema without x-partition-fields. process_record(record). Assert key contains fallback date segment (e.g. year=.../month=.../day=...) from date_fn.
  - **hive_partitioned true, x-partition-fields [enum, date]:** Schema x-partition-fields ["r","d"]; record r="x", d=datetime(2024,3,11). Process record. Assert key (or _build_key_for_record result) contains "x" and "year=2024/month=03/day=11" in order.
  - **Partition change closes handle:** Two records with different partition paths; process first then second. Assert two distinct keys and that handle was closed (e.g. via mock or written blobs; black-box).
- **File:** `loaders/target-gcs/tests/test_partition_key_generation.py`
  - Replace tests that used partition_date_field with hive_partitioned and schema with x-partition-fields.
  - Add: hive_partitioned true without x-partition-fields → path is fallback date.
  - Add: multiple streams, different x-partition-fields order; assert keys differ per stream.
  - Keep tests that assert ParserError when date string is invalid (via schema+record path builder).
- Use deterministic date_fn (e.g. `date_fn=lambda: datetime(2024,3,11)`) in tests. Assert keys/paths only; no "called_once" or log assertions.

## Testing Needed

- The above items are the tests to add or update. Run full test suite and fix any regressions; ensure SAMPLE_CONFIG or test configs include hive_partitioned: false or omit so standard target tests still pass.
