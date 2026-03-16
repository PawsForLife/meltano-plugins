# AI Context — target-gcs Component

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.7 |
| Last Updated | 2026-03-16 |
| Tags | target-gcs, singer, target, GCS, meltano, loader, destination, sink, RecordSink |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, data flow), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands, env), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (typing, testing), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (target, destination, streams, Sink, config file, SCHEMA/RECORD/STATE), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md) (tap component) |

**Summary:** Singer **target** (loader) that reads SCHEMA, RECORD, and STATE messages from stdin and loads record data into **Google Cloud Storage** as the destination. One **sink** per stream; writes JSONL using **config file** settings (bucket, key prefix, optional `hive_partitioned` and chunking). Key format is fixed by internal constants; no user-configurable key template.

---

## Module Overview

| Module / File | Responsibility |
|---------------|----------------|
| `target_gcs/target.py` | Target class, config JSON schema, default sink binding, and sink creation with optional storage client injection. Entry point for the CLI. |
| `target_gcs/sinks.py` | `GCSSink`: selects one of SimplePath, DatedPath, or PartitionedPath from config and schema; delegates `process_record` and lifecycle to `_extraction_pattern`. |
| `target_gcs/paths/base.py` | `BasePathPattern`: shared key prefix, effective template, JSONL write, rotation at limit, flush/close; subclasses implement key building and handle lifecycle. |
| `target_gcs/paths/simple.py` | `SimplePath`: single path per stream, one handle; `{date}` from config `date_format` and injection `extraction_date`; rotation at `max_records_per_file`. |
| `target_gcs/paths/dated.py` | `DatedPath`: Hive-style by extraction date only; partition path from `extraction_date` via `DEFAULT_PARTITION_DATE_FORMAT`; rotation at limit. |
| `target_gcs/paths/partitioned.py` | `PartitionedPath`: schema-driven Hive from `x-partition-fields`; partition path per record via `hive_path(record)`; on partition change closes handle and resets state; rotation at limit within partition. |
| `target_gcs/paths/_partitioned/hive.py` | `get_hive_path_generator(partition_fields, schema)`: returns list of `(field_name, fn)`; fn is `date_as_partition` or `string_as_partition` per field schema. |
| `target_gcs/paths/_partitioned/string_functions.py` | `date_as_partition`, `string_as_partition`: format partition path segments; date uses `DEFAULT_PARTITION_DATE_FORMAT`; date parsing via `dateutil.parser.parse` (raises `dateutil.parser.ParserError` when unparseable). |
| `target_gcs/paths/_partitioned/validators.py` | `is_date_field(field_definition)`: true when schema type/format is date or date-time (used to choose date vs string segment). |
| `target_gcs/paths/_types.py` | `PathType` enum: SIMPLE, DATED, PARTITIONED (for typing; not used in runtime selection). |
| `target_gcs/helpers/partition_schema.py` | `validate_partition_fields_schema`, `validate_partition_date_field_schema`, `_assert_field_required_and_non_null_type`: schema validation for partition fields. |
| `target_gcs/helpers/json_parsing.py` | `_json_default`: orjson default for `Decimal` → float; raises `TypeError` for other non-serializable types. |
| `target_gcs/constants.py` | `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`, `DEFAULT_PARTITION_DATE_FORMAT`. |

Package root: `loaders/target-gcs/`. Source package: `target_gcs/`. No shared code with the tap; communication is Singer JSONL on stdin.

---

## Public Interfaces

### Constants (`target_gcs.constants`)

- **`PATH_SIMPLE`**, **`PATH_DATED`**, **`PATH_PARTITIONED`**: Path templates for SimplePath, DatedPath, PartitionedPath. Tokens: `{stream}`, `{date}`, `{hive_path}`.
- **`FILENAME_TEMPLATE`**: `"{timestamp}.jsonl"` — filename segment; timestamp-only chunking (no `{chunk_index}`).
- **`DEFAULT_PARTITION_DATE_FORMAT`**: `"year=%Y/month=%m/day=%d"` (Hive-style). Single source of truth for partition date formatting. Used by `DatedPath` and `_partitioned.string_functions` for date segments in partition paths.

### GCSTarget (`target_gcs.target`)

- **Base**: `singer_sdk.target_base.Target`
- **CLI**: `target-gcs` → `target_gcs.target:GCSTarget.cli` (from `pyproject.toml`).
- **Config schema** (`config_jsonschema`): Declared with `singer_sdk.typing`:
  - `bucket_name` (string, **required**): GCS bucket name.
  - `key_prefix` (string, optional): Prepended to the generated object key; normalized (no leading `//`, leading `/` stripped).
  - `max_records_per_file` (integer, optional): When set and > 0, the sink rotates to a new file after that many records per stream; when 0 or omitted, one file per stream per run. Chunking uses timestamp-only filenames; `{timestamp}` is refreshed per chunk.
  - `hive_partitioned` (boolean, optional, default false): When true, Hive-style partitioning from stream schema `x-partition-fields` or extraction date; path built per record via `hive_path(record)` in PartitionedPath or extraction date in DatedPath.
- **Sink**: `default_sink_class = GCSSink`.
- **Sink creation**: Overrides `get_sink()` and `_add_sink_with_client()` so each sink receives `storage_client=self._storage_client`. `_storage_client` is set in `__init__`: from `kwargs["storage_client"]` if provided, else `Client()`. Tests use a subclass that injects a recording client (e.g. `GCSTargetWithRecordingStorage` with `RecordingGCSClient`).

The path patterns read `date_format` from config for the `{date}` token (e.g. SimplePath). It is not in `config_jsonschema`; Meltano or external config file can pass it (e.g. `meltano.yml` settings). Default in code: `%Y-%m-%d`.

### GCSSink (`target_gcs.sinks`)

- **Base**: `singer_sdk.sinks.RecordSink`
- **Constructor**: `GCSSink(target, stream_name, schema, key_properties, storage_client, *, time_fn=None, extraction_date=None)`. Same contract as SDK `RecordSink` plus: `storage_client` (required), optional `time_fn` (callable returning float for deterministic filenames), optional `extraction_date` (datetime; when None, defaults to `datetime.today()`). In `__init__`, the sink selects one extraction pattern from config and schema and stores it in `_extraction_pattern` (type `BasePathPattern`).
- **Pattern selection**: `hive_partitioned` false or unset → `SimplePath`; `hive_partitioned` true + non-empty `x-partition-fields` in schema → `PartitionedPath`; `hive_partitioned` true + no/empty `x-partition-fields` → `DatedPath`. Same injectables (`time_fn`, `storage_client`, `extraction_date`) are passed into the pattern constructor.
- **Delegation**: `process_record(record, context)` and `close()` delegate to `_extraction_pattern.process_record` and `_extraction_pattern.close()`. `key_name` and `storage_client` delegate to the pattern's `current_key` and `storage_client`. Key naming, GCS handle (smart_open), JSONL write, and chunk rotation are implemented in the base and concrete pattern classes in `target_gcs.paths` (base, simple, dated, partitioned).
- **Class attribute**: `max_size = 1000` (batch size hint for SDK; records are still written per `process_record` call).
- **Key tokens** (implemented in pattern classes): `{stream}`, `{date}`, `{hive_path}`, `{timestamp}`. Path and filename come from constants `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; key building uses `filename_for_current_file()` and `full_key(path, filename)`. Chunking is timestamp-only (no `{chunk_index}`).
- **Output**: `output_format` = `"jsonl"`. Each record is written as one JSON line; pattern classes use base `write_record_as_jsonl` (orjson, `_json_default`). Unparseable partition date strings in PartitionedPath raise `dateutil.parser.ParserError` (from `date_as_partition` in `_partitioned/string_functions.py`).

### Authentication

- No `credentials_file` or path in config. GCS client uses Application Default Credentials only (`Client()`). For a key file, set `GOOGLE_APPLICATION_CREDENTIALS` in the environment.

---

## Lifecycle / Entry Points

1. **Invocation**: `target-gcs` CLI (or Meltano `meltano run <tap> target-gcs`). Config via config file `--config <path>` or Meltano-injected config.
2. **Input**: Singer JSONL on stdin (SCHEMA, RECORD, STATE messages). Target parses and routes by message type.
3. **Sink creation**: One `GCSSink` per stream; target's `get_sink()` creates sinks via `_add_sink_with_client()`, passing `storage_client=self._storage_client`. The target does not pass `time_fn` or `extraction_date`; sinks use `datetime.today()` and `time.time` unless a custom sink subclass or test injects them.
4. **Key and handle**: On first use, each sink computes `key_name` (with timestamp and date at that time) and opens `gcs_write_handle`.
5. **Writing**: Each RECORD is passed to `process_record` and written immediately as one JSONL line to the open handle.
6. **Shutdown / sink drain**: When the target closes a sink (stream switch or exit), the SDK drains it; open handles are closed (flush if supported, then close). State may be written to stdout per Singer spec when sinks drain.

---

## Hive Partitioning Behaviour

**Selection rule**: `hive_partitioned` false or unset → **SimplePath** (single path per stream, no partition). `hive_partitioned` true + non-empty `x-partition-fields` → **PartitionedPath** (partition path per record from schema). `hive_partitioned` true + no/empty `x-partition-fields` → **DatedPath** (extraction date only).

- **DatedPath**: Partition path is the run/extraction date via `DEFAULT_PARTITION_DATE_FORMAT` (e.g. `year=2024/month=03/day=11`). One logical partition per run; chunking rotates within it. Uses injected `extraction_date` (or `datetime.today()` when not injected).
- **PartitionedPath**: Partition path per record via `hive_path(record)` from stream schema `x-partition-fields` and the record. Path order = array order. Every segment is `key=value`: literal segments `field_name=value` (path-safe); date segments `year=.../month=.../day=...`. **Date-parseable** is determined by `is_date_field()` (schema type/format date or date-time); native `datetime`/`date` are date segments. Unparseable date strings raise `dateutil.parser.ParserError`. On partition change the pattern closes the handle and resets state; when the same partition returns, the next write gets a new key (new file). Chunking rotates within the current partition.

### Partition fields validation (sink init)

When `hive_partitioned` is true and the stream schema has non-empty `x-partition-fields`, the sink validates at init via `validate_partition_fields_schema` in `target_gcs.helpers.partition_schema`. Each listed field must be in `schema["properties"]`, in `schema["required"]`, and have at least one non-null type. On failure a `ValueError` is raised with the stream name, field name, and reason. `validate_partition_date_field_schema` (for partition_date_field) applies the same "field in properties, required, non-null type" checks. The shared logic is in `_assert_field_required_and_non_null_type(...)`; both validators call it and are exported from `target_gcs.helpers`.

---

## Extension Points

- **Custom sink class**: Subclass `GCSTarget` and set `default_sink_class` to a custom sink (e.g. different key naming or format).
- **Storage client injection**: Pass `storage_client` in `GCSTarget(**kwargs)` (e.g. `GCSTargetWithRecordingStorage` in tests) so sinks receive it via `_add_sink_with_client`. Or pass `storage_client` when constructing a sink directly (e.g. in tests). For deterministic keys in tests, also pass `time_fn` and `extraction_date` to `GCSSink`.
- **Extraction patterns**: Custom sinks can subclass or replace the path pattern classes (`SimplePath`, `DatedPath`, `PartitionedPath`) or extend `BasePathPattern` in `target_gcs.paths` for different key or partition semantics (e.g. custom key template, partition layout, or output format). GCSSink selects the pattern in `__init__`; a custom sink can inject a different pattern or factory.
- **Partition resolution**: Custom patterns can implement `hive_path(record)` or `path_for_record(record)`; key building lives in the pattern classes via `full_key(path, filename)`.
- **Config**: Add new options in `GCSTarget.config_jsonschema` and read them in the sink or pattern via config. Example: add `date_format` to the schema for consistency with Meltano.

---

## Examples

### Minimal config (schema-only)

```json
{
  "bucket_name": "my-bucket"
}
```

Key format is fixed: SimplePath → `{stream}/{date}/{timestamp}.jsonl`; DatedPath/PartitionedPath → `{stream}/{hive_path}/{timestamp}.jsonl`. `key_prefix` is prepended if set.

### Full sample config (Meltano / file)

```json
{
  "bucket_name": "datateer-managed-prt-prod-raw-data",
  "key_prefix": "prt-test/triton",
  "date_format": "%Y-%m-%d"
}
```

Resulting key pattern: `prt-test/triton/{stream}/{date}/{timestamp}.jsonl` (SimplePath) or `prt-test/triton/{stream}/{hive_path}/{timestamp}.jsonl` (DatedPath/PartitionedPath) with tokens replaced.

### Test sink construction (from tests)

Tests use fixtures from `conftest.py`: `sample_config`, `fixed_time_fn`, `fixed_date`, `recording_storage_client`. Target is created with injected storage client; sink is constructed with optional `time_fn` and `extraction_date` for deterministic keys:

```python
target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
sink = GCSSink(
    target=target,
    stream_name="my_stream",
    schema={"properties": {}},
    key_properties=[],
    storage_client=recording_storage_client,
    time_fn=fixed_time_fn,
    extraction_date=fixed_date,
)
sink.process_record({"id": 1}, {})
assert re.match(r"my_stream/\d{4}-\d{2}-\d{2}/\d+\.jsonl", sink.key_name)
```

### Running as part of a pipeline

```bash
# Via Meltano (config from meltano.yml; from project root)
meltano run restful-api-tap target-gcs

# Or from loaders/target-gcs with venv active and a config file
target-gcs --config /path/to/your-config.json < singer_output.jsonl
```

---

## Tests

- **Location**: `loaders/target-gcs/tests/unit/` (mirrors source: `paths/`, `helpers/`, `fixtures/`).
- **test_target.py**: SDK standard target tests via `get_target_test_class(GCSTargetWithRecordingStorage, config=SAMPLE_CONFIG)`. `GCSTargetWithRecordingStorage` (in `conftest.py`) subclasses `GCSTarget` and passes `storage_client=RecordingGCSClient()` in `__init__`. `_TARGET_TEST_CONFIG = {"bucket_name": "test-bucket"}`.
- **test_sinks.py**: Key naming, config schema, GCS client behaviour, chunking rotation, record integrity, Decimal serialization (`_json_default`), non-serializable type (`TypeError`). Uses `GCSSink(..., storage_client=recording_storage_client, time_fn=..., extraction_date=...)` with `RecordingGCSClient` from fixtures; no patching of smart_open or Client.
- **paths/test_base.py**: BasePathPattern key prefix, filename, full_key, write/rotation, flush/close.
- **paths/test_simple.py**, **paths/test_dated.py**: SimplePath/DatedPath key shape, rotation at limit.
- **paths/test_partitioned.py**: PartitionedPath init validation, partition path from record, handle lifecycle on partition change, rotation at limit, `dateutil.parser.ParserError` propagation, `current_key`.
- **paths/_partitioned/test_string_functions.py**: `date_as_partition`, `string_as_partition` behaviour and ParserError.
- **helpers/test_partition_schema.py**, **helpers/test_json_parsing.py**: Partition schema validators and `_json_default`.
- **fixtures/recording_gcs_client.py**: `RecordingGCSClient` implements the interface expected by smart_open's GCS backend; tests assert via `get_written_paths()` and `get_written_content()`.

Tests use `RecordingGCSClient` for GCS so no real bucket is required. Black-box style: assert on `key_name`, written payloads, and client/handle behaviour, not internal call counts.
