# Testing — Schema-driven Hive Partitioning

## Strategy (TDD)

- Write failing tests first for each unit (validator, path builder, then sink behaviour). Implement until tests pass. No tests that assert on "called_once" or log output; assert on return values, raised exceptions, or observable output (e.g. key name, path string, written payload).
- Black-box: validate functionality (path string, key format, validation errors), not internal calls.

## 1. validate_partition_fields_schema

**File**: `loaders/target-gcs/tests/helpers/test_partition_schema.py`

| Test | What | Why |
|------|------|-----|
| Valid — all fields in properties, required, non-nullable | Schema with properties A,B; required [A,B]; partition_fields [A,B]; types string and number. Call validator; no exception. | Ensures valid schema passes. |
| Missing field in properties | partition_fields includes "C"; "C" not in schema["properties"]. Expect ValueError with stream name and "not in schema". | Ensures invalid field is rejected. |
| Field not required | Schema required [A]; partition_fields [A,B]; B in properties but not in required. Expect ValueError "must be required". | Ensures partition fields must be required. |
| Required not a list | schema["required"] = "A" or missing. Expect ValueError. | Ensures schema shape is valid. |
| Null-only type | Property type "null" or ["null"]. Expect ValueError "null-only". | Ensures non-nullable. |
| Mixed optional and required | required [A]; partition_fields [A,B]; B optional. Expect ValueError for B. | Covers typical failure. |

Use `pytest.raises(ValueError)` and assert message contains stream_name and reason substring.

## 2. get_partition_path_from_schema_and_record

**File**: `loaders/target-gcs/tests/helpers/test_partition_path.py`

| Test | What | Why |
|------|------|-----|
| No x-partition-fields | schema = {} or no key. record any. fallback_date fixed. Expect return = fallback_date.strftime(partition_date_format). | Fallback when schema has no partition fields. |
| Empty x-partition-fields | schema = {"x-partition-fields": []}. Expect same as no key. | Empty list = fallback. |
| Single date field (value datetime) | schema with x-partition-fields ["dt"]; properties dt format "date-time"; record dt = datetime(2024,3,11). Expect segment year=2024/month=03/day=11. | Date segment from datetime. |
| Single date field (value string ISO) | record dt = "2024-03-11"; format "date". Expect same segment. | Date segment from string. |
| Single literal field | x-partition-fields ["region"]; record region = "eu"; no date format. Expect "eu". | Literal segment. |
| Two fields enum then date | x-partition-fields ["region","dt"]; record region="eu", dt=datetime(2024,3,11). Expect "eu/year=2024/month=03/day=11". | Path order. |
| Two fields date then enum | x-partition-fields ["dt","region"]; same record. Expect "year=2024/month=03/day=11/eu". | Path order. |
| Literal with slash | record region = "a/b"; expect path-safe segment (e.g. "a_b"). | Sanitization. |
| Unparseable date string | record dt = "not-a-date"; schema suggests date. Expect ParserError. | No silent fallback for bad date. |

Use fixed fallback_date (e.g. datetime(2024, 1, 15)) and default or explicit partition_date_format for deterministic strings.

## 3. Sink — config and init

**File**: `loaders/target-gcs/tests/test_sinks.py`

| Test | What | Why |
|------|------|-----|
| Config schema has hive_partitioned | Load GCSTarget.config_jsonschema; assert "hive_partitioned" in properties; type boolean; not required (or default false). | Config is present. |
| Config schema no partition_date_field | Assert "partition_date_field" not in config_jsonschema["properties"]. | Old config removed. |
| Sink init with hive_partitioned and invalid x-partition-fields | build_sink with config hive_partitioned true, schema with x-partition-fields ["missing"] but "missing" not in properties. Expect ValueError when sink is created (or on first use if validation is lazy). | Validation runs and fails. |
| Sink init with hive_partitioned and valid x-partition-fields | Schema has x-partition-fields ["a"]; a in properties and required, non-null. No exception. | Happy path init. |

## 4. Sink — key and path output (black-box)

**File**: `loaders/target-gcs/tests/test_sinks.py` or `test_partition_key_generation.py`

| Test | What | Why |
|------|------|-----|
| hive_partitioned false | build_sink(hive_partitioned false). process_record(record). Assert key does not contain partition segments from record (flat or date-only from run). | Default behaviour unchanged. |
| hive_partitioned true, no x-partition-fields | Schema without x-partition-fields. process_record(record). Assert key contains fallback date segment (e.g. year=.../month=.../day=...) from date_fn. | Current date path. |
| hive_partitioned true, x-partition-fields [enum, date] | Schema x-partition-fields ["r","d"]; record r="x", d=datetime(2024,3,11). Process record. Assert key (or _build_key_for_record result) contains "x" and "year=2024/month=03/day=11" in order. | Multi-field path. |
| Partition change closes handle | Two records with different partition paths. Process first then second. Assert two distinct keys and that handle was closed (e.g. via mock or written blobs). | Lifecycle. |

Use build_sink(..., date_fn=lambda: datetime(2024,3,11)) for deterministic fallback.

## 5. test_partition_key_generation.py updates

- Replace tests that relied on partition_date_field with hive_partitioned and schema containing x-partition-fields.
- Add test: multiple streams, each with different x-partition-fields order; assert keys differ per stream.
- Keep tests that assert ParserError when date string is invalid (now via schema+record path builder).

## Integration

- No end-to-end test against real GCS required; existing mocks (Client, smart_open) suffice. Standard target tests (test_core.py) run with config that may include hive_partitioned; ensure SAMPLE_CONFIG or test configs are updated so standard tests still pass (e.g. add hive_partitioned: false or omit).

## Regression Gate

- All tests must pass; no test marked xfail unless explicitly expected failure. Fix any failing test before task complete.
