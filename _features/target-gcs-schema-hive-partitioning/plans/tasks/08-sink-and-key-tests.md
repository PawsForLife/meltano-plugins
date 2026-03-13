# Task 08 — Sink and key generation tests (plan)

## Overview

This task adds and updates **black-box tests** for sink behaviour and key generation after the schema-driven Hive partitioning implementation (tasks 01–07). It validates that:

- With `hive_partitioned: false` (or omitted), keys and behaviour match the existing flat / non-hive semantics.
- With `hive_partitioned: true` and no `x-partition-fields`, the key contains a fallback-date partition segment.
- With `hive_partitioned: true` and `x-partition-fields`, the key contains segments from the record in schema order (literal and/or date segments).
- When the partition path changes between records, the handle is closed and a new key is used (observable via distinct keys / mock open calls).

**Scope:** Test code only. No new production code. Depends on task 07 (sink process_record dispatch and record processing).

**Constraints:** Black-box only (assert keys/paths and observable behaviour; no "called_once" or log assertions). Use deterministic `date_fn` (e.g. `lambda: datetime(2024, 3, 11)`). Ensure standard target tests still pass (SAMPLE_CONFIG has no partition config; default `hive_partitioned: false` is sufficient).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/test_sinks.py` | Modify: (1) Config schema tests: assert `hive_partitioned` present (boolean, optional); assert `partition_date_field` and `partition_date_format` no longer in schema (or tests removed). (2) Init validation: replace partition_date_field-based validation tests with hive_partitioned + x-partition-fields (invalid field → ValueError; valid → success). (3) Add key/path tests: hive_partitioned false → key without record-driven partition segments; hive_partitioned true without x-partition-fields → key contains fallback date segment; hive_partitioned true with x-partition-fields [enum, date] → key contains literal and date segments in order; partition change → two distinct keys and handle closed (e.g. mock_open.call_count or written blobs). |
| `loaders/target-gcs/tests/test_partition_key_generation.py` | Modify: (1) `build_sink`: accept optional schema and stream_name; when `hive_partitioned` is true, build schema with `x-partition-fields` and required properties as needed; remove partition_date_field-based schema construction. (2) Replace tests that used `partition_date_field` with equivalents using `hive_partitioned: true` and schema `x-partition-fields`. (3) Add: hive_partitioned true without x-partition-fields → path is fallback date. (4) Add: multiple streams, different x-partition-fields order → keys differ per stream. (5) Keep ParserError test: unparseable date in partition field (via schema+record path builder) raises ParserError. |

No new files. No changes to `test_core.py` or SAMPLE_CONFIG (default `hive_partitioned: false` is sufficient).

---

## Test Strategy

- **TDD context:** Tests in this task validate the behaviour implemented in tasks 05–07. They are written/updated in task 08 so that the implementer can run them after completing tasks 01–07 to confirm correctness.
- **Order:** (1) Config schema and init validation in test_sinks.py. (2) Key/path and partition-change tests in test_sinks.py. (3) test_partition_key_generation.py build_sink and test updates; then new cases (fallback path, multiple streams, ParserError).
- **Assertions:** Keys/paths (string content, containment, order of segments). Exception type and message content (ValueError, ParserError). Observable handle behaviour (e.g. two records with different partition paths → two open calls, two distinct keys). No assertions on "called_once", call counts for internal helpers, or log output.
- **Determinism:** Use `date_fn=lambda: datetime(2024, 3, 11)` (or similar) and fixed `time_fn` where key timestamp matters.
- **Regression:** Run full target-gcs test suite; fix any failing test before considering the task complete.

---

## Implementation Order

1. **test_sinks.py — Config schema**
   - Replace or remove tests that assert `partition_date_field` and `partition_date_format` in config_jsonschema.
   - Add test: config_jsonschema has `hive_partitioned` (boolean, optional / default false).
   - Add or adjust test: config validates with `hive_partitioned: true` and with `hive_partitioned: false` (or omitted).

2. **test_sinks.py — Init validation**
   - Replace partition_date_field init validation tests with hive_partitioned + x-partition-fields:
     - hive_partitioned true, x-partition-fields with field missing from schema → ValueError (message contains stream name and field/reason).
     - hive_partitioned true, x-partition-fields with invalid field (e.g. not required, null-only) → ValueError.
     - hive_partitioned true, x-partition-fields valid (all in properties, required, non-nullable) → sink constructs.
     - hive_partitioned false or unset → sink constructs with any schema (no x-partition-fields validation).

3. **test_sinks.py — _get_effective_key_template**
   - Update tests that reference partition_date_field to use hive_partitioned and schema with x-partition-fields where applicable (effective template = hive default when hive_partitioned true and no user template; non-partition default when hive_partitioned false).

4. **test_sinks.py — Key/path behaviour (black-box)**
   - hive_partitioned false: build_sink(hive_partitioned false). process_record(record). Assert key does not contain partition segments derived from record (flat or existing behaviour).
   - hive_partitioned true, no x-partition-fields: schema without x-partition-fields. process_record(record). Assert key contains fallback date segment (e.g. year=.../month=.../day=...) from date_fn.
   - hive_partitioned true, x-partition-fields [enum, date]: schema x-partition-fields ["r","d"]; record r="x", d=datetime(2024,3,11). Process record. Assert key (or path passed to open) contains "x" and "year=2024/month=03/day=11" in order.
   - Partition change closes handle: two records with different partition paths; process first then second. Assert two distinct keys (e.g. from mock_open call args) and that two open calls occurred (handle closed and reopened).

5. **test_partition_key_generation.py — build_sink and schema**
   - Update build_sink to use config `hive_partitioned` instead of `partition_date_field`. When hive_partitioned true, accept optional schema (with x-partition-fields) and stream_name; default schema to include required fields for x-partition-fields when provided.
   - Ensure date_fn and time_fn can be passed for deterministic keys.

6. **test_partition_key_generation.py — Replace partition_date_field tests**
   - Migrate each test that used partition_date_field to hive_partitioned true and schema with x-partition-fields (e.g. single date field in x-partition-fields for _build_key_for_record and process_record tests).
   - Keep _build_key_for_record tests that assert key shape (hive default, user template, {hive} alias, fallback path); adapt to partition_path obtained from get_partition_path_from_schema_and_record semantics (path still passed into _build_key_for_record).

7. **test_partition_key_generation.py — New cases**
   - hive_partitioned true without x-partition-fields: path is fallback date (e.g. key contains fallback date segment).
   - Multiple streams, different x-partition-fields order: two sinks (or two process_record flows) with different stream schemas (e.g. ["region","dt"] vs ["dt","region"]); assert keys differ and contain expected segment order per stream.
   - Keep test_sink_raises_parser_error_when_partition_field_unparseable: record with unparseable date in a partition field → ParserError (path builder or sink propagates it).

8. **Regression and standards**
   - Run `uv run pytest` in loaders/target-gcs; fix any failing test.
   - Ensure no test asserts on internal call counts or log lines; only keys, paths, exceptions, and observable mock behaviour (e.g. open call count for partition-change test).

---

## Validation Steps

1. From `loaders/target-gcs/`, run: `uv run pytest tests/test_sinks.py tests/test_partition_key_generation.py -v`.
2. All tests in these two files pass.
3. Run full suite: `uv run pytest`; no failures (excluding explicitly xfail).
4. Lint and type-check: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy target_gcs`.

---

## Documentation Updates

- **This task:** No README or meltano.yml changes (task 09).
- **Optional:** In CHANGELOG or task list, note that sink and key-generation tests were updated for schema-driven Hive partitioning (hive_partitioned, x-partition-fields).
