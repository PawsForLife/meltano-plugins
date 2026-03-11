# Implementation Plan — Dependencies: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## External Dependencies

No new third-party packages. Existing dependencies are sufficient:

- **singer_sdk:** Target and RecordSink base; config schema via `th.PropertiesList`, `th.Property`, `th.IntegerType`. No API change.
- **smart_open:** GCS write handle; used as today. Rotation only closes and reopens; no new API.
- **google.cloud.storage (Client):** Used for GCS transport; no change.
- **orjson:** Record serialization; no change.
- **Python stdlib:** `time`, `datetime`, `collections.defaultdict` — already used in sinks.

---

## Internal Dependencies

- **Config:** `GCSTarget.config_jsonschema` defines `max_records_per_file`; the sink reads it via `self.config.get("max_records_per_file", 0)`. Target must be instantiated with config that passes validation (bucket_name required; new key optional).
- **Sink:** Depends only on `gcs_target.sinks` and `gcs_target.target` (for GCSTarget when building the sink in tests). No dependency on tap or other loaders.

---

## System Requirements

- Unchanged: Python version per target-gcs `pyproject.toml` (e.g. `>=3.8,<4.0`). No new system or runtime requirements.

---

## Environment and Configuration

- **Config file:** Singer config file (or Meltano-injected config) may include `max_records_per_file` (integer). Omission or 0 means chunking disabled.
- **State file:** No change to state file handling; chunking is per-run and does not persist chunk index or record count in state.
- **Key naming convention:** If chunking is enabled and the user wants unique keys per chunk, the convention should include `{chunk_index}` (e.g. `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl`). Existing conventions without `{chunk_index}` still work; timestamp alone may collide if two chunks start in the same second.

---

## Meltano

- If the project documents target-gcs in `meltano.yml` (e.g. under `loaders`), add a setting for `max_records_per_file` so users can configure it via Meltano. No new Meltano version or plugin discovery change required.
