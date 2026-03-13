# AI Context — target-gcs Component

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.4 |
| Last Updated | 2026-03-13 |
| Tags | target-gcs, singer, target, GCS, meltano, loader, destination, sink, RecordSink |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, data flow), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands, env), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (typing, testing), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (target, destination, streams, Sink, config file, SCHEMA/RECORD/STATE), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md) (tap component) |

**Summary:** Singer **target** (loader) that reads SCHEMA, RECORD, and STATE messages from stdin and loads record data into **Google Cloud Storage** as the destination. One **sink** per stream; writes JSONL using **config file** settings (bucket, key prefix, key naming, optional `hive_partitioned` and chunking).

---

## Module Overview

| Module / File | Responsibility |
|---------------|----------------|
| `target_gcs/target.py` | Target class, config JSON schema, default sink binding, and sink creation with optional storage client injection. Entry point for the CLI. |
| `target_gcs/sinks.py` | `GCSSink`: key naming, GCS write handle (smart_open), record writing (JSONL via orjson), partition path resolution, and chunk rotation. |

Package root: `loaders/target-gcs/`. Source package: `target_gcs/`. No shared code with the tap; communication is Singer JSONL on stdin.

---

## Public Interfaces

### `get_partition_path_from_schema_and_record` (`target_gcs.helpers.partition_path`)

- **Signature**: `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format) -> str`
- **Role**: Build partition path from stream schema `x-partition-fields` and record. Path order = array order. **Date-parseable** is determined only by the field's schema having `format: "date"` or `"date-time"`; string values are never parsed as dates without that format. Native `datetime`/`date` values are always treated as date segments. When format is absent, values are emitted as literal segments (path-safe: `str(value).replace("/", "_")`). Date-parseable → `year=.../month=.../day=...`; other → literal folder. Used by `GCSSink` when `hive_partitioned` is true. Exported from `target_gcs.helpers`. Unparseable date strings (when format is date/date-time) raise `ParserError`. Fallback date used when field missing or empty.
- **Constant**: `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"` (Hive-style).

### GCSTarget (`target_gcs.target`)

- **Base**: `singer_sdk.target_base.Target`
- **CLI**: `target-gcs` → `target_gcs.target:GCSTarget.cli` (from `pyproject.toml`).
- **Config schema** (`config_jsonschema`): Declared with `singer_sdk.typing`:
  - `bucket_name` (string, **required**): GCS bucket name.
  - `key_prefix` (string, optional): Prepended to the generated object key; normalized (no leading `//`, leading `/` stripped).
  - `key_naming_convention` (string, optional): Template for the object key. When omitted, the effective default is conditional: if `hive_partitioned` is true, default is `{stream}/{partition_date}/{timestamp}.jsonl`; if false or omitted, default is `{stream}_{timestamp}.jsonl`.
  - `max_records_per_file` (integer, optional): When set and > 0, the sink rotates to a new file after that many records per stream; when 0 or omitted, one file per stream per run. When chunking is enabled, the key token `{chunk_index}` (0-based) is available and `{timestamp}` is refreshed per chunk.
  - `hive_partitioned` (boolean, optional, default false): When true, Hive-style partitioning from stream schema `x-partition-fields` or current date; path built per record via `get_partition_path_from_schema_and_record`.
- **Sink**: `default_sink_class = GCSSink`.
- **Sink creation**: Overrides `get_sink()` and `_add_sink_with_client()` so each sink receives `storage_client=self._storage_client`. `_storage_client` is `None` by default (sink then uses `Client()`); tests set it to a mock (e.g. `GCSTargetWithMockStorage`).

The sink also reads `date_format` from config (used for the `{date}` token). It is not in `config_jsonschema`; Meltano or external config file can pass it (e.g. `meltano.yml` settings). Default in code: `%Y-%m-%d`.

### GCSSink (`target_gcs.sinks`)

- **Base**: `singer_sdk.sinks.RecordSink`
- **Constructor**: `GCSSink(target, stream_name, schema, key_properties, *, time_fn=None, date_fn=None, storage_client=None)` — same contract as SDK `RecordSink`; optional `time_fn` (callable returning float) for key generation; optional `date_fn` (callable returning datetime) for partition fallback and tests; optional `storage_client` for injection (when `None`, sink uses `Client()`).
- **Partition state**: When `hive_partitioned` is true, the sink keeps one active handle and `_current_partition_path`; key is derived per record via `_build_key_for_record(record, partition_path)`. On partition change the sink closes the handle and clears key/partition state; when the partition "returns," the next write gets a new key (new file), not a reopen.
- **Class attribute**: `max_size = 1000` (batch size hint for SDK; records are still written per `process_record` call).
- **Key naming** (`key_name` property, `_build_key_for_record`): When `hive_partitioned` is false, `key_name` is computed once per sink (recomputed after rotation when chunking is on). When `hive_partitioned` is true, `key_name` returns the current key after a write (or empty); per-record keys are built by `_build_key_for_record` from stream, partition_date, timestamp, and optionally chunk_index. Uses `key_prefix` + `key_naming_convention` (or default). Tokens:
  - `{stream}` — stream name.
  - `{date}` — `datetime.today().strftime(config.get("date_format", "%Y-%m-%d"))`; used when `hive_partitioned` is false.
  - `{partition_date}` — partition path per record (e.g. `year=2024/month=03/day=11`); only when `hive_partitioned` is true.
  - `{hive}` — alias for `{partition_date}` when `hive_partitioned` is true.
  - `{timestamp}` — Unix time at key resolution (refreshed at start of each chunk when chunking is enabled).
  - `{chunk_index}` — 0-based chunk index; only when `max_records_per_file` is set and > 0.
- **GCS handle** (`gcs_write_handle` property): Opens via `smart_open.open("gs://{bucket}/{key_name}", "wb", transport_params={"client": client})`. Client is `storage_client` if provided, else `Client()` (ADC only).
- **Output**: `output_format` = `"jsonl"`. Each record is written as one JSON line with `orjson.dumps(..., option=orjson.OPT_APPEND_NEWLINE, default=_json_default)`. `_json_default` serializes `decimal.Decimal` as float; other non-JSON types raise `TypeError`.
- **Record processing**: `process_record(self, record: dict, context: dict) -> None` writes the record to the open handle. When `hive_partitioned` is true: partition path is resolved per record via `get_partition_path_from_schema_and_record` (schema `x-partition-fields` or fallback date). Unparseable partition date strings raise `ParserError`.

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

When `hive_partitioned` is true, the sink uses one active write handle. On each record it resolves the partition path via `get_partition_path_from_schema_and_record` from the stream schema `x-partition-fields` and the record (or fallback date when `x-partition-fields` is absent or empty). Path order = array order. **Date-parseable** is determined only by schema `format: "date"` or `"date-time"` for that field; there is no inference from value type or dateutil-parseable string when format is not set. Native `datetime`/`date` are still processed as date segments. Date-parseable values → `year=.../month=.../day=...`; other values → literal folder (path-unsafe chars replaced). Unparseable date strings (when format is date/date-time) raise `ParserError`. When the partition path changes, the sink closes the handle and clears key/partition state; when the same partition "returns" later, the next write gets a new key (new file). Chunking (`max_records_per_file`) rotates within the current partition.

### Partition fields validation (sink init)

When `hive_partitioned` is true and the stream schema has non-empty `x-partition-fields`, the sink validates at init via `validate_partition_fields_schema` in `target_gcs.helpers.partition_schema`. Each listed field must be in `schema["properties"]`, in `schema["required"]`, and non-nullable. On failure a `ValueError` is raised with the stream name, field name, and reason.

---

## Extension Points

- **Custom sink class**: Subclass `GCSTarget` and set `default_sink_class` to a custom sink (e.g. different key naming or format).
- **Storage client injection**: Set `target._storage_client` before sync (e.g. in a subclass like `GCSTargetWithMockStorage`) so sinks receive it; or pass `storage_client` when constructing a sink directly (e.g. in tests).
- **Partition resolution / key building**: Custom sinks can reuse `get_partition_path_from_schema_and_record` or override `_build_key_for_record` for different partition or key semantics.
- **Key naming**: Override `GCSSink.key_name` or the logic that builds it to change template, tokens, or prefix handling.
- **Output format**: Override `GCSSink.output_format` and the write logic in `process_record` (e.g. Parquet, CSV). Current code path assumes JSONL.
- **Config**: Add new options in `GCSTarget.config_jsonschema` and read them in the sink via `self.config.get(...)`. Example: add `date_format` to the schema for consistency with Meltano.

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
- **test_partition_key_generation.py**: `get_partition_path_from_schema_and_record` and partition path in key; `_build_key_for_record` with `hive_partitioned` and `x-partition-fields`; partition change and partition-return; chunking within partition; fallback date; ParserError.

Tests use mocks for GCS (`patch("target_gcs.sinks.Client")`, `patch("target_gcs.sinks.smart_open.open")`) so no real bucket is required. Black-box style: assert on `key_name`, written payloads, and client/handle call arguments, not internal call counts.
