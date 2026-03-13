# Implementation — Schema-driven Hive Partitioning

## Implementation Order (TDD)

1. **Models / interfaces first**: No new Pydantic/dataclass models required; schema and record are dicts; partition_fields is `list[str]`. Interfaces are the two new functions (path builder, validator) with signatures as in `interfaces.md`.
2. **Tests first per component**: Write tests for `validate_partition_fields_schema`, then for `get_partition_path_from_schema_and_record`, then for sink behaviour (config, init validation, key/path output). Implement after each test batch.
3. **Config and sink wiring**: Add `hive_partitioned` to target config; remove old partition config; sink switches on `hive_partitioned` and calls new helpers.
4. **Docs and Meltano**: Update README and meltano.yml.

## Step-by-Step

### Step 1: Validator — tests then implementation

- **File**: `loaders/target-gcs/tests/helpers/test_partition_schema.py`
  - Add tests for `validate_partition_fields_schema`:
    - Pass: all fields in properties, in required, non-nullable (e.g. type `"string"` or `["string","null"]` with non-null present).
    - Fail: field not in properties; field not in required; field null-only (type `"null"` or `["null"]`); required not a list.
  - Each test: call validator with stream_name, schema dict, list of field names; assert no exception or `pytest.raises(ValueError)` and message contains stream name and reason.
- **File**: `loaders/target-gcs/target_gcs/helpers/partition_schema.py`
  - Add `validate_partition_fields_schema(stream_name, schema, partition_fields)`; loop over partition_fields, reuse same checks as current validator (in properties, in required, non-null types). Raise ValueError with clear message. Keep `validate_partition_date_field_schema` for now if still referenced; otherwise remove after sink is updated.

### Step 2: Path builder — tests then implementation

- **File**: `loaders/target-gcs/tests/helpers/test_partition_path.py`
  - Add tests for `get_partition_path_from_schema_and_record`:
    - Schema missing `x-partition-fields` or empty → returns fallback_date formatted with partition_date_format.
    - Single date field (schema format "date" or value date/datetime/parseable string) → one segment YEAR=.../MONTH=.../DAY=....
    - Single literal field (non-date string or number) → one segment = path-safe value.
    - Multiple fields: [enum, date] → `enum_value/year=.../month=.../day=...`; [date, enum] → `year=.../month=.../day=.../enum_value`.
    - Literal value containing `/`: sanitize to path-safe (e.g. replace with `_`).
    - Unparseable date string → expect ParserError (or document if we fall back to literal; selected solution says dateutil parse, so ParserError).
  - Use fixed `fallback_date` and optional `partition_date_format` in tests for deterministic output.
- **File**: `loaders/target-gcs/target_gcs/helpers/partition_path.py`
  - Add `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`. Default constant can be imported from sinks or defined in partition_path (avoid circular import). Implement: read x-partition-fields; if missing/empty return fallback_date strftime; else for each field get value, decide date vs literal (schema format, type of value, dateutil parse), append segment (date → reuse existing strftime logic from get_partition_path_from_record), join with `/`. Add internal helper `_segment_for_field(schema, record, field_name, partition_date_format)` or inline. For literal, sanitize: replace `/` in str(value) with `_`.

### Step 3: Helper exports

- **File**: `loaders/target-gcs/target_gcs/helpers/__init__.py`
  - Export `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema`. Add to `__all__`. If sink no longer uses `get_partition_path_from_record` and `validate_partition_date_field_schema`, remove from exports (or keep for backward compat if any external caller exists; feature says no backward compat required, so remove when unused).

### Step 4: Config schema (target)

- **File**: `loaders/target-gcs/target_gcs/target.py`
  - In `config_jsonschema`: add `th.Property("hive_partitioned", th.BooleanType, required=False, default=False, description="When true, enable Hive partitioning from stream schema (x-partition-fields) or current date.")`. Remove `th.Property("partition_date_field", ...)` and `th.Property("partition_date_format", ...)`.

### Step 5: Sink — partition enablement and init validation

- **File**: `loaders/target-gcs/target_gcs/sinks.py`
  - Replace all use of `partition_date_field` with `hive_partitioned`. Where sink checks `if self.config.get("partition_date_field")`, use `if self.config.get("hive_partitioned")`.
  - In `__init__`: when `self.config.get("hive_partitioned")` and `self.schema.get("x-partition-fields")` (and is a non-empty list), call `validate_partition_fields_schema(self.stream_name, self.schema, self.schema["x-partition-fields"])`. Set `_current_partition_path` when `hive_partitioned` is true (same as before).
  - Remove references to `partition_date_field` and `partition_date_format` from init and _get_effective_key_template. For effective key template: when `hive_partitioned` use hive default template; else use non-partition default or user override.
  - Import: add `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema` from `.helpers`; remove or keep `get_partition_path_from_record` and `validate_partition_date_field_schema` only if still used (they will not be once partition path is always from schema+record when hive_partitioned).

### Step 6: Sink — record processing

- **File**: `loaders/target-gcs/target_gcs/sinks.py`
  - In `_process_record_partition_by_field` (or renamed to reflect hive_partitioned): obtain partition_path via `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=self.config.get("partition_date_format") or DEFAULT_PARTITION_DATE_FORMAT)`. Note: config no longer has partition_date_format per selected solution (removed); use DEFAULT_PARTITION_DATE_FORMAT only, or add optional config for format if we want user override (selected solution says "default in code"; use constant).
  - Rest of method unchanged: compare partition_path to _current_partition_path; on change close handle and clear state; build key with _build_key_for_record(record, partition_path); write record.
  - Rename method if desired (e.g. _process_record_hive_partitioned) for clarity; call site in process_record must call this when hive_partitioned.

### Step 7: Sink — process_record dispatch

- **File**: `loaders/target-gcs/target_gcs/sinks.py`
  - In `process_record`: when `self.config.get("hive_partitioned")` call the partition-by-field path (new or renamed method); else call _process_record_single_or_chunked.

### Step 8: Tests — sink and key generation

- **File**: `loaders/target-gcs/tests/test_sinks.py`
  - Config: assert config_jsonschema has `hive_partitioned` (boolean, optional); assert no `partition_date_field` / `partition_date_format` (or they are removed).
  - Sink init: when hive_partitioned true and schema has x-partition-fields with invalid field (missing from schema, optional, null-only), expect ValueError.
  - Key/path: build_sink with hive_partitioned true and schema with x-partition-fields; process_record with a record; assert key (or written path) contains expected segments (black-box: e.g. key contains "region_a" and "year=2024" for enum and date).
- **File**: `loaders/target-gcs/tests/test_partition_key_generation.py`
  - Update tests that used partition_date_field to use hive_partitioned and schema with x-partition-fields. Add cases: hive_partitioned true without x-partition-fields → path is fallback date; with x-partition-fields → path from fields in order; multiple streams, different field orders. Assert keys/paths, not call counts.

### Step 9: Meltano and README

- **File**: `loaders/target-gcs/meltano.yml`
  - Add setting `hive_partitioned` (boolean, default false). Remove partition_date_field and partition_date_format if present.
- **File**: `loaders/target-gcs/README.md`
  - Document hive_partitioned and x-partition-fields; path order and semantics (date → YEAR/MONTH/DAY, non-date → literal folder); required and non-nullable rules; literal sanitization (e.g. slash replaced).

## File Summary

| File | Action |
|------|--------|
| `target_gcs/helpers/partition_schema.py` | Add validate_partition_fields_schema; optionally remove or keep validate_partition_date_field_schema |
| `target_gcs/helpers/partition_path.py` | Add get_partition_path_from_schema_and_record; internal date vs literal and segment building; reuse existing date formatting |
| `target_gcs/helpers/__init__.py` | Export new functions; update __all__ |
| `target_gcs/target.py` | Add hive_partitioned; remove partition_date_field, partition_date_format |
| `target_gcs/sinks.py` | Use hive_partitioned; init validation with new validator; record path from get_partition_path_from_schema_and_record; _get_effective_key_template on hive_partitioned |
| `tests/helpers/test_partition_schema.py` | Tests for validate_partition_fields_schema |
| `tests/helpers/test_partition_path.py` | Tests for get_partition_path_from_schema_and_record |
| `tests/test_sinks.py` | Config schema, init validation, key/path assertions |
| `tests/test_partition_key_generation.py` | Hive partition key tests with schema + record |
| `meltano.yml` | hive_partitioned setting; remove old partition settings |
| `README.md` | Document hive_partitioned and x-partition-fields |

## Dependency Injection

- Sink already has `date_fn` for fallback date; use it in get_partition_path_from_schema_and_record when called from sink (sink passes self.fallback which is from date_fn or datetime.today()). No new DI for path builder.
- partition_date_format: selected solution removed from config; use DEFAULT_PARTITION_DATE_FORMAT in path builder and sink. If we later add optional config, sink can pass it into the path builder.

## Constants

- Keep `DEFAULT_PARTITION_DATE_FORMAT` in sinks.py; partition_path can import from a shared place or define same value to avoid circular import. Prefer: define in partition_path.py and have sinks import from helpers, or keep in sinks and pass into get_partition_path_from_schema_and_record (current signature has default "year=%Y/month=%m/day=%d" in interfaces.md). Use default parameter in partition_path so sinks need not pass it unless we add config later.
