# Impacted Systems — target-gcs-partition-field-validation

## Summary

Validation of `partition_date_field` against the stream schema affects the target-gcs loader only. No other repo components (taps, shared libs, CI) are modified.

## Components

### 1. `loaders/target-gcs/target_gcs/sinks.py` — GCSSink

- **Role**: RecordSink that writes records to GCS; uses `partition_date_field` from config to build partition paths via `get_partition_path_from_record`.
- **Impact**: Sink must run validation when `partition_date_field` is set. Validation runs after the sink has the stream schema (i.e. after `super().__init__` in `__init__`), using the schema already on the sink.
- **Interfaces**: `GCSSink.__init__` (add validation call when config has `partition_date_field`). No change to `process_record`, `_process_record_partition_by_field`, or public method signatures.

### 2. `loaders/target-gcs/target_gcs/target.py` — GCSTarget, sink creation

- **Role**: Creates sinks via `get_sink` / `_add_sink_with_client`; passes stream `schema` into the sink constructor.
- **Impact**: None. Schema is already passed; no API change. Validation is internal to the sink.

### 3. `loaders/target-gcs/target_gcs/helpers/partition_path.py` — partition path resolution

- **Role**: `get_partition_path_from_record` reads the record field and parses dates (string via dateutil; datetime/date passed through).
- **Impact**: Optional: a small helper that checks if a schema property is “date-parseable” could live here or in a dedicated validation module. No change to `get_partition_path_from_record` signature or behaviour.

### 4. Tests

- **`loaders/target-gcs/tests/test_sinks.py`**: Add or extend tests that build a sink with `partition_date_field` and a given stream schema; assert `ValueError` when the field is missing or type is not date-parseable, and no error when valid.
- **`loaders/target-gcs/tests/helpers/test_partition_path.py`**: If validation logic is in helpers (e.g. a new validation function), add unit tests for that function (missing field, null-only type, allowed types).

## Data flow

- **Config**: `partition_date_field` is already read in the sink from `self.config` (and defined in `GCSTarget.config_jsonschema`).
- **Schema**: Stream schema is provided to the sink in `__init__` and stored by the Singer SDK base as `self.schema` (and `self.original_schema`). So validation has access to `self.schema["properties"]` once the sink is constructed.
- **Failure**: Validation raises a clear `ValueError` (or a small custom exception) with stream name, field name, and reason; no silent fallback.

## Out of scope

- **Tap or mapper**: No change; they only send SCHEMA/RECORD messages.
- **Config schema**: `partition_date_field` remains optional; no new required config.
- **State / bookmarks**: Unchanged.
