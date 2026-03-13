# AI Context — target-gcs Component

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.5 |
| Last Updated | 2026-03-13 |
| Tags | target-gcs, singer, target, GCS, meltano, loader, destination, sink, RecordSink |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, data flow), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands, env), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (typing, testing), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (target, destination, streams, Sink, config file, SCHEMA/RECORD/STATE), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md) (tap component) |

**Summary:** Singer **target** (loader) that reads SCHEMA, RECORD, and STATE messages from stdin and loads record data into **Google Cloud Storage** as the destination. One **sink** per stream; writes JSONL using **config file** settings (bucket, key prefix, key naming, optional `hive_partitioned` and chunking).

---

## Module Overview

| Module / File | Responsibility |
|---------------|----------------|
| `target_gcs/target.py` | Target class, config JSON schema, default sink binding, and sink creation with optional storage client injection. Entry point for the CLI. |
| `target_gcs/sinks.py` | `GCSSink`: selects one of SimplePath, DatedPath, or PartitionedPath from config and schema; delegates `process_record` and lifecycle to `_extraction_pattern`. |
| `target_gcs/paths/base.py` | `BasePathPattern`: shared key prefix, effective template, JSONL write, rotation at limit, flush/close; subclasses implement key building and handle lifecycle. |
| `target_gcs/paths/simple.py` | `SimplePath`: single path per stream, one handle; rotation at `max_records_per_file`. |
| `target_gcs/paths/dated.py` | `DatedPath`: Hive-style by extraction date only; partition path from extraction_date via `DEFAULT_PARTITION_DATE_FORMAT`; rotation at limit. |
| `target_gcs/paths/partitioned.py` | `PartitionedPath`: schema-driven Hive from `x-partition-fields`; partition path per record via `hive_path(record)`; on partition change closes handle and resets state; rotation at limit within partition. |

Package root: `loaders/target-gcs/`. Source package: `target_gcs/`. No shared code with the tap; communication is Singer JSONL on stdin.

---

## Public Interfaces

### Constants (`target_gcs.constants`)

- **`DEFAULT_PARTITION_DATE_FORMAT`**: `"year=%Y/month=%m/day=%d"` (Hive-style). Single source of truth for partition date formatting. Used by `DatedPath` and `_partitioned.string_functions` for date segments in partition paths.

### GCSTarget (`target_gcs.target`)

- **Base**: `singer_sdk.target_base.Target`
- **CLI**: `target-gcs` → `target_gcs.target:GCSTarget.cli` (from `pyproject.toml`).
- **Config schema** (`config_jsonschema`): Declared with `singer_sdk.typing`:
  - `bucket_name` (string, **required**): GCS bucket name.
  - `key_prefix` (string, optional): Prepended to the generated object key; normalized (no leading `//`, leading `/` stripped).
  - `key_naming_convention` (string, optional): Template for the object key. When omitted, the effective default is conditional: if `hive_partitioned` is true, default is `{stream}/{partition_date}/{timestamp}.jsonl`; if false or omitted, default is `{stream}_{timestamp}.jsonl`.
  - `max_records_per_file` (integer, optional): When set and > 0, the sink rotates to a new file after that many records per stream; when 0 or omitted, one file per stream per run. When chunking is enabled, the key token `{chunk_index}` (0-based) is available and `{timestamp}` is refreshed per chunk.
  - `hive_partitioned` (boolean, optional, default false): When true, Hive-style partitioning from stream schema `x-partition-fields` or extraction date; path built per record via `hive_path(record)` in PartitionedPath or extraction date in DatedPath.
- **Sink**: `default_sink_class = GCSSink`.
- **Sink creation**: Overrides `get_sink()` and `_add_sink_with_client()` so each sink receives `storage_client=self._storage_client`. `_storage_client` is `None` by default (sink then uses `Client()`); tests set it to a mock (e.g. `GCSTargetWithMockStorage`).

The sink also reads `date_format` from config (used for the `{date}` token). It is not in `config_jsonschema`; Meltano or external config file can pass it (e.g. `meltano.yml` settings). Default in code: `%Y-%m-%d`.

### GCSSink (`target_gcs.sinks`)

- **Base**: `singer_sdk.sinks.RecordSink`
- **Constructor**: `GCSSink(target, stream_name, schema, key_properties, *, time_fn=None, date_fn=None, storage_client=None)` — same contract as SDK `RecordSink`; optional `time_fn`, `date_fn`, `storage_client` for injection. In `__init__`, the sink selects one extraction pattern from config and schema and stores it in `_extraction_pattern` (type `BasePathPattern`).
- **Pattern selection**: `hive_partitioned` false or unset → `SimplePath`; `hive_partitioned` true + non-empty `x-partition-fields` in schema → `PartitionedPath`; `hive_partitioned` true + no/empty `x-partition-fields` → `DatedPath`. Same injectables (time_fn, date_fn, storage_client) are passed into the pattern constructor.
- **Delegation**: `process_record(record, context)` and `close()` delegate to `_extraction_pattern.process_record` and `_extraction_pattern.close()`. `key_name` and `storage_client` delegate to the pattern’s `current_key` and `storage_client`. Key naming, GCS handle (smart_open), JSONL write, and chunk rotation are implemented in the base and concrete pattern classes in `target_gcs.paths` (base, simple, dated, partitioned).
- **Class attribute**: `max_size = 1000` (batch size hint for SDK; records are still written per `process_record` call).
- **Key tokens** (implemented in pattern classes): `{stream}`, `{date}`, `{partition_date}` / `{hive}`, `{timestamp}`, `{chunk_index}` (when chunking). Behaviour is unchanged from pre-refactor; see path classes for details.
- **Output**: `output_format` = `"jsonl"`. Each record is written as one JSON line; pattern classes use base `write_record_as_jsonl` (orjson, `_json_default`). Unparseable partition date strings in PartitionedPath raise `ParserError`.

### Authentication

- No `credentials_file` or path in config. Schema and tests assert the config file has no `credentials_file`.
- GCS client uses Application Default Credentials only (`Client()`). For a key file, set `GOOGLE_APPLICATION_CREDENTIALS` in the environment.

---

## Lifecycle / Entry Points

1. **Invocation**: `target-gcs` CLI (or Meltano `meltano run <tap> target-gcs`). Config via config file `--config <path>` or Meltano-injected config.
2. **Input**: Singer JSONL on stdin (SCHEMA, RECORD, STATE messages). Target parses and routes by message type.
3. **Sink creation**: One `GCSSink` per stream; target’s `get_sink()` creates sinks via `_add_sink_with_client()`, passing `storage_client=self._storage_client`.
4. **Key and handle**: On first use, each sink computes `key_name` (with timestamp and date at that time) and opens `gcs_write_handle`.
5. **Writing**: Each RECORD is passed to `process_record` and written immediately as one JSONL line to the open handle.
6. **Shutdown / sink drain**: When the target closes a sink (stream switch or exit), the SDK drains it; open handles are closed (flush if supported, then close). State may be written to stdout per Singer spec when sinks drain.

---

## Hive partitioning behaviour

**Selection rule**: `hive_partitioned` false or unset → **SimplePath** (single path per stream, no partition). `hive_partitioned` true + non-empty `x-partition-fields` → **PartitionedPath** (partition path per record from schema). `hive_partitioned` true + no/empty `x-partition-fields` → **DatedPath** (extraction date only).

- **DatedPath**: Partition path is the run/extraction date via `DEFAULT_PARTITION_DATE_FORMAT` (e.g. `year=2024/month=03/day=11`). One logical partition per run; chunking rotates within it.
- **PartitionedPath**: Partition path per record via `hive_path(record)` from stream schema `x-partition-fields` and the record. Path order = array order. Every segment is `key=value`: literal segments `field_name=value` (path-safe); date segments `year=.../month=.../day=...`. **Date-parseable** is determined only by schema `format: "date"` or `"date-time"`; native `datetime`/`date` are date segments. Unparseable date strings (when format is date/date-time) raise `ParserError`. On partition change the pattern closes the handle and resets state; when the same partition returns, the next write gets a new key (new file). Chunking rotates within the current partition.

### Partition fields validation (sink init)

When `hive_partitioned` is true and the stream schema has non-empty `x-partition-fields`, the sink validates at init via `validate_partition_fields_schema` in `target_gcs.helpers.partition_schema`. Each listed field must be in `schema["properties"]`, in `schema["required"]`, and have at least one non-null type. On failure a `ValueError` is raised with the stream name, field name, and reason. `validate_partition_date_field_schema` (for partition_date_field) applies the same “field in properties, required, non-null type” checks. The shared logic is in `_assert_field_required_and_non_null_type(stream_name, field_name, schema, *, field_label=..., no_type_reason=..., null_only_reason=...)`; both validators call it and are exported from `target_gcs.helpers`.

---

## Extension Points

- **Custom sink class**: Subclass `GCSTarget` and set `default_sink_class` to a custom sink (e.g. different key naming or format).
- **Storage client injection**: Set `target._storage_client` before sync (e.g. in a subclass like `GCSTargetWithMockStorage`) so sinks receive it; or pass `storage_client` when constructing a sink directly (e.g. in tests).
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

Key name defaults to `{stream}_{timestamp}.jsonl` when `hive_partitioned` is false; when `hive_partitioned` is true and `key_naming_convention` is omitted, default is `{stream}/{partition_date}/{timestamp}.jsonl` (with optional `key_prefix` if set).

### Full sample config (Meltano / file)

```json
{
  "bucket_name": "datateer-managed-prt-prod-raw-data",
  "key_prefix": "prt-test/triton",
  "date_format": "%Y-%m-%d",
  "key_naming_convention": "{stream}/export_date={date}/{timestamp}.jsonl"
}
```

Resulting key pattern: `prt-test/triton/{stream}/export_date={date}/{timestamp}.jsonl` with `{stream}`, `{date}`, and `{timestamp}` replaced.

### Test sink helper (from tests)

```python
def build_sink(config=None, time_fn=None, date_fn=None, storage_client=None):
    if config is None:
        config = {}
    default_config = {"bucket_name": "test-bucket"}
    config = {**default_config, **config}
    kwargs = {}
    if time_fn is not None:
        kwargs["time_fn"] = time_fn
    if date_fn is not None:
        kwargs["date_fn"] = date_fn
    if storage_client is not None:
        kwargs["storage_client"] = storage_client
    return GCSSink(
        GCSTarget(config=config), "my_stream", {"properties": {}},
        key_properties=config, **kwargs
    )
```

Used in tests to construct a sink with optional overrides; `key_properties=config` is test-specific (normally key_properties come from the stream schema).

### Running as part of a pipeline

```bash
# Via Meltano (config from meltano.yml; from project root)
meltano run restful-api-tap target-gcs

# Or from loaders/target-gcs with venv active and a config file
target-gcs --config /path/to/your-config.json < singer_output.jsonl
```

---

## Tests

- **Location**: `loaders/target-gcs/tests/`
- **test_core.py**: Runs SDK standard target tests via `get_target_test_class(GCSTargetWithMockStorage, config=SAMPLE_CONFIG)`. `GCSTargetWithMockStorage` sets `self._storage_client = MagicMock()` so no real GCS is used. `SAMPLE_CONFIG = {"bucket_name": "test-bucket"}`.
- **test_sinks.py**: Key naming, config schema, GCS client behaviour, chunking rotation, record integrity, Decimal serialization (`_json_default`), and non-serializable type (`TypeError`). Uses `build_sink(..., storage_client=...)` and mocks `Client` / `smart_open.open`.
- **test_partition_key_generation.py**: Partition path in key; `_build_key_for_record` with `hive_partitioned` and `x-partition-fields`; partition change and partition-return; chunking within partition; extraction date; ParserError.

Tests use mocks for GCS (`patch("target_gcs.sinks.Client")`, `patch("target_gcs.sinks.smart_open.open")`) so no real bucket is required. Black-box style: assert on `key_name`, written payloads, and client/handle call arguments, not internal call counts.
