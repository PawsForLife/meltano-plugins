# target-gcs-schema-hive-partitioning — Archive Summary

## The request

target-gcs (loader/target) previously controlled partitioning via config-only parameters (`partition_date_field`, `partition_date_format`). The goal was to simplify configuration and support a single tap with multiple streams writing to one target-gcs instance, with partitioning driven by **schema metadata** and a single boolean flag.

**Config:** Add `hive_partitioned: bool` (default `false`). When `true`, enable Hive partitioning; no config-driven partition field names.

**Schema extension:** Use `x-partition-fields: ["field1", "field2", ...]` on the **stream** schema. If present when `hive_partitioned` is true, use these fields (in order) to build the Hive partition path; otherwise use current date.

**Partition field rules:** Each field in `x-partition-fields` must be required and non-nullable in the schema.

**Field semantics:** Date-parseable values (prefer schema format hint, fallback to parse) → existing Hive date structure (`YEAR=.../MONTH=.../DAY=...`). Otherwise treat as enum: value as literal folder name. Path order follows `x-partition-fields` (e.g. `[my_enum, my_date]` → `my_enum_value/YEAR=.../MONTH=.../DAY=.../timestamp.yml`).

**Testing:** Black-box tests for default (no hive path), hive with/without `x-partition-fields`, required/non-nullable validation, multiple partition fields and order, and path output—no assertions on internal calls or logs.

---

## Planned approach

**Solution:** Internal implementation only: extend existing helpers and sink logic; no new external libraries. Reuse `dateutil` and existing Hive date format.

**Architecture:**

- **GCSTarget** (`target.py`): Config schema adds `hive_partitioned` (bool, default false); remove `partition_date_field` and `partition_date_format`.
- **GCSSink** (`sinks.py`): Use `hive_partitioned` to choose partition vs flat/chunked. When true: at init, if schema has non-empty `x-partition-fields`, call `validate_partition_fields_schema`; per record, call `get_partition_path_from_schema_and_record`; pass result to existing key/handle lifecycle (partition change → close handle, clear state).
- **partition_path** (`helpers/partition_path.py`): New `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format)`. Read `x-partition-fields`; if missing/empty return fallback date formatted; else for each field append one segment (date → Hive date path, else path-safe literal); join with `/`. Literal sanitization: replace `/` with `_`. Propagate `ParserError` for unparseable date strings.
- **partition_schema** (`helpers/partition_schema.py`): New `validate_partition_fields_schema(stream_name, schema, partition_fields)`. For each field: in properties, in required, non-nullable; raise `ValueError` with stream name and reason on first failure.
- **helpers/__init__.py**: Export the two new functions; legacy exports kept until sink migration, then removed.

**Task breakdown (9 tasks, TDD):**

1. **01** — Validator tests and implementation (`validate_partition_fields_schema` + tests in `test_partition_schema.py`).
2. **02** — Path builder tests and implementation (`get_partition_path_from_schema_and_record` + tests in `test_partition_path.py`).
3. **03** — Helper exports (`__init__.py`: new exports and `__all__`).
4. **04** — Config schema (target: add `hive_partitioned`, remove old partition properties; tests in `test_sinks.py`).
5. **05** — Sink init and validation (wire `hive_partitioned`, init-time `validate_partition_fields_schema` when `x-partition-fields` present, effective key template, imports).
6. **06** — Sink record processing (partition path via `get_partition_path_from_schema_and_record`, method renamed to `_process_record_hive_partitioned`).
7. **07** — Sink `process_record` dispatch on `hive_partitioned` (hive path vs single/chunked).
8. **08** — Sink and key generation tests (black-box: keys/paths for hive off, hive+fallback date, hive+`x-partition-fields`, partition change; `test_partition_key_generation.py` migrated to `hive_partitioned` + schema).
9. **09** — Meltano and README (`meltano.yml` setting, README config and Hive section, optional AI context and CHANGELOG).

---

## What was implemented

All nine tasks were completed; full target-gcs test suite (116 tests) passes.

- **Tasks 01–02:** `validate_partition_fields_schema` and `get_partition_path_from_schema_and_record` implemented with full test coverage (valid/invalid schema, path from fallback date, single/multiple fields, date vs literal, literal slash sanitization, unparseable date → `ParserError`).
- **Task 03:** Helpers `__init__.py` exports both new functions; legacy exports retained where still used.
- **Task 04:** Target config schema has `hive_partitioned` (boolean, optional, default false); `partition_date_field` and `partition_date_format` removed; config tests updated.
- **Tasks 05–07:** Sink uses `hive_partitioned` everywhere; init runs `validate_partition_fields_schema` when `hive_partitioned` is true and schema has non-empty `x-partition-fields`; record path from `get_partition_path_from_schema_and_record` with `DEFAULT_PARTITION_DATE_FORMAT`; method `_process_record_hive_partitioned`; `process_record` dispatches on `hive_partitioned` (hive path vs single/chunked).
- **Task 08:** Black-box tests added/updated in `test_sinks.py` and `test_partition_key_generation.py`: hive off, hive+fallback date, hive+`x-partition-fields` (literal + date order), partition change (two keys/handle close); `build_sink` and tests migrated to `hive_partitioned` and schema; ParserError and multiple streams/order covered.
- **Task 09:** `meltano.yml` adds `hive_partitioned` (default false), removes old partition settings; README documents config, `x-partition-fields`, path order/semantics, validation, and removal note; AI context and CHANGELOG updated.

**Outcome:** One tap, multiple streams, one target-gcs; partitioning is driven by config (`hive_partitioned`) and stream schema (`x-partition-fields`) with no config-driven partition field list. No new dependencies; behaviour validated by black-box tests.
