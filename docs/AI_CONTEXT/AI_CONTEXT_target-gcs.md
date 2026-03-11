# AI Context — target-gcs Component

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.1 |
| Last Updated | 2026-03-11 |
| Tags | target-gcs, singer, target, GCS, meltano, loader, destination, sink |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, data flow), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands, env), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (typing, testing), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (target, destination, streams, Sink, config file, SCHEMA/RECORD/STATE), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md) (tap component) |

**Summary:** Singer **target** (loader) that reads SCHEMA, RECORD, and STATE messages from stdin and loads record data into **Google Cloud Storage** as the destination. One **sink** per stream; writes JSONL objects using config file settings (bucket, key prefix, key naming).

---

## Module Overview

| Module / File | Responsibility |
|---------------|----------------|
| `gcs_target/target.py` | Target class, config JSON schema, and default sink binding. Entry point for the CLI. |
| `gcs_target/sinks.py` | `GCSSink`: key naming, GCS write handle (smart_open), and record writing (JSONL via orjson). |

Package root: `loaders/target-gcs/`. Source package: `gcs_target/`. No shared code with the tap; communicates via Singer JSONL on stdin.

---

## Public Interfaces

### GCSTarget (`gcs_target.target`)

- **Base**: `singer_sdk.target_base.Target`
- **CLI**: `target-gcs` → `gcs_target.target:GCSTarget.cli` (from `pyproject.toml`).
- **Config schema** (`config_jsonschema`): Declared with `singer_sdk.typing`:
  - `bucket_name` (string, **required**): GCS bucket name.
  - `key_prefix` (string, optional): Prepended to the generated object key; normalized (no leading `//`, leading `/` stripped).
  - `key_naming_convention` (string, optional): Template for the object key. When omitted, effective default is `{stream_name}_{timestamp}.jsonl`.
  - `max_records_per_file` (integer, optional): When set and > 0, the sink rotates to a new file after that many records per stream; when 0 or omitted, one file per stream per run. When chunking is enabled, the key token `{chunk_index}` (0-based) is available and `{timestamp}` is refreshed per chunk.
  - `partition_date_field` (string, optional): Record property name used for the partition path; when set, partition-by-field is enabled. Example: `created_at`, `updated_at`.
  - `partition_date_format` (string, optional): strftime format for partition path segments; default in code is Hive-style (e.g. `year=%Y/month=%m/day=%d`).
- **Sink**: `default_sink_class = GCSSink`.

The sink also reads `date_format` from config (used for the `{date}` token). It is not in `config_jsonschema`; Meltano or external config file can pass it (e.g. `meltano.yml` settings). Default in code: `%Y-%m-%d`.

### GCSSink (`gcs_target.sinks`)

- **Base**: `singer_sdk.sinks.RecordSink`
- **Constructor**: `GCSSink(target, stream_name, schema, key_properties, *, time_fn=None, date_fn=None)` — same contract as SDK `RecordSink`; optional `time_fn` (callable returning float) for key generation; optional `date_fn` (callable returning datetime) for partition fallback and tests.
- **Partition-by-field state**: When `partition_date_field` is set, the sink keeps one active handle and `_current_partition_path`; key is derived per record via `_build_key_for_record(record, partition_path)`. On partition change the sink closes the handle and clears key/partition state; when the partition "returns," the next write gets a new key (new file), not a reopen.
- **Class attribute**: `max_size = 1000` (batch size hint for SDK; records are still written per `process_record` call).
- **Key naming** (`key_name` property, `_build_key_for_record`): When `partition_date_field` is unset, `key_name` is computed once per sink (recomputed after rotation when chunking is on). When partition-by-field is on, `key_name` returns the current key after a write (or empty); per-record keys are built by `_build_key_for_record` from stream, partition_date, timestamp, and optionally chunk_index. Uses `key_prefix` + `key_naming_convention` (or default). Tokens:
  - `{stream}` — stream name.
  - `{date}` — `datetime.today().strftime(config.get("date_format", "%Y-%m-%d"))`; used when partition-by-field is off.
  - `{partition_date}` — partition path per record (e.g. `year=2024/month=03/day=11`); available only when `partition_date_field` is set; not available when partition-by-field is off.
  - `{timestamp}` — Unix time at key resolution (refreshed at start of each chunk when chunking is enabled).
  - `{chunk_index}` — 0-based chunk index; available only when `max_records_per_file` is set and > 0.
- **GCS handle** (`gcs_write_handle` property): Opens once per sink via `smart_open.open("gs://{bucket}/{key_name}", "wb", transport_params={"client": client})`. Client is `google.cloud.storage.Client()` with no arguments (ADC only).
- **Output**: `output_format` = `"jsonl"`. Each record is written as one JSON line with `orjson.dumps(..., option=orjson.OPT_APPEND_NEWLINE)`.
- **Record processing**: `process_record(self, record: dict, context: dict) -> None` writes the record to `gcs_write_handle`. With partition-by-field: partition path is resolved per record (helper `get_partition_path_from_record`); missing or invalid partition field uses run date as fallback (formatted with `partition_date_format`).

### Authentication

- No `credentials_file` or path in config. Schema and tests assert the config file has no `credentials_file`.
- GCS client uses Application Default Credentials only (`Client()`). For a key file, set `GOOGLE_APPLICATION_CREDENTIALS` in the environment.

---

## Lifecycle / Entry Points

1. **Invocation**: `target-gcs` CLI (or Meltano `meltano run <tap> target-gcs`). Config via config file `--config <path>` or Meltano-injected config.
2. **Input**: Singer JSONL on stdin (SCHEMA, RECORD, STATE messages). Target parses and routes by message type.
3. **Sink creation**: One `GCSSink` per stream (SDK creates sinks from stream schemas/catalog).
4. **Key and handle**: On first use, each sink computes `key_name` (with timestamp and date at that time) and opens `gcs_write_handle`.
5. **Writing**: Each RECORD is passed to `process_record` and written immediately as one JSONL line to the open handle.
6. **Shutdown / sink drain**: When the target closes a sink (stream switch or exit), the SDK drains it; open handles are closed by process teardown. No explicit flush API in the sink; state may be written to stdout per Singer spec when sinks drain.

---

## Partition-by-field behaviour

When `partition_date_field` is set, the sink uses one active write handle. On each record it resolves the partition path from the record (or run date if the field is missing or unparseable). When the partition path changes, the sink closes the handle and clears key/partition state; when the same partition "returns" later, the next write gets a new key (new file). Chunking (`max_records_per_file`) rotates within the current partition. Fallback for missing or invalid partition field: run date formatted with `partition_date_format`.

---

## Extension Points

- **Custom sink class**: Subclass `GCSTarget` and set `default_sink_class` to a custom sink (e.g. different key naming or format).
- **Partition resolution / key building**: Custom sinks can override partition resolution (e.g. call or replace `get_partition_path_from_record`) or key building (`_build_key_for_record`) if needed.
- **Key naming**: Override `GCSSink.key_name` (or the logic that builds it) to change template, tokens, or prefix handling.
- **Output format**: Override `GCSSink.output_format` and the write logic in `process_record` (e.g. Parquet, CSV). Current code path assumes JSONL.
- **Config**: Add new options in `GCSTarget.config_jsonschema` and read them in the sink via `self.config.get(...)`. Example: add `date_format` to the schema for consistency with Meltano.
- **GCS client**: To inject or mock the client, you would need to change the sink (e.g. accept a client factory or pass client via target config); today the sink instantiates `Client()` directly.

---

## Examples

### Minimal config (schema-only)

```json
{
  "bucket_name": "my-bucket"
}
```

Key name defaults to `{stream_name}_{unix_timestamp}.jsonl` (with optional `key_prefix` if set).

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
def build_sink(config=None):
    if config is None:
        config = {}
    default_config = {"bucket_name": "test-bucket"}
    config = {**default_config, **config}
    return GCSSink(
        GCSTarget(config=config), "my_stream", {"properties": {}}, key_properties=config
    )
```

Used in tests to construct a sink with optional overrides; `key_properties=config` is test-specific (normally key_properties come from the stream schema).

### Running as part of a pipeline

```bash
# From loaders/target-gcs with venv active
target-gcs --config sample.config.json < singer_output.jsonl

# Or via Meltano (from project root)
meltano run restful-api-tap target-gcs
```

---

## Tests

- **Location**: `loaders/target-gcs/tests/`
- **test_core.py**: Runs SDK `get_standard_target_tests(GCSTarget, config=SAMPLE_CONFIG)`. `SAMPLE_CONFIG` is currently minimal (TODO in repo).
- **test_sinks.py**: Key naming and GCS client behaviour:
  - Default key pattern, prefix, no leading slash, custom `key_naming_convention`, `{stream}`, `{date}`, `{timestamp}`, and `date_format`.
  - Config must not expose `credentials_file`.
  - GCS client is created with `Client()` only (no credentials path); same when `GOOGLE_APPLICATION_CREDENTIALS` is set.

Tests use mocks for GCS (`patch("gcs_target.sinks.Client")`) so no real bucket is required. Black-box style: assert on `key_name` and client call arguments, not internal call counts.
