# Master Plan — Interfaces: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**See:** [overview.md](overview.md), [architecture.md](architecture.md)

---

## Config schema (GCSTarget)

**File:** `loaders/target-gcs/gcs_target/target.py`

Add to `config_jsonschema` (Singer SDK `th.PropertiesList`):

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `partition_date_field` | string | No | Record property name for partition path (e.g. `created_at`, `updated_at`). When set, partition-by-field is enabled. |
| `partition_date_format` | string | No | strftime-style format for Hive path segment. Default: `year=%Y/month=%m/day=%d`. Used to format the parsed date. |

Existing properties (`bucket_name`, `key_prefix`, `key_naming_convention`, `max_records_per_file`) unchanged. No new required properties.

---

## Key naming tokens

When `partition_date_field` is set:

- **New token:** `{partition_date}` — Replaced with the partition path string for the **current record** (e.g. `year=2024/month=03/day=11`). Not available when `partition_date_field` is unset; existing templates that do not use it are unchanged.
- **Existing tokens:** `{stream}`, `{timestamp}`, `{chunk_index}` (when chunking). `{date}` remains run-date based; when partition-by-field is on, templates typically use `{partition_date}` instead of `{date}` for the partition segment.

When `partition_date_field` is unset: `{partition_date}` is not substituted (or token is not advertised); behaviour equals current (run-date `{date}`, one key per stream per run or per chunk).

---

## Partition resolution

**Contract:** From a record, config subset, and fallback datetime, produce a partition path string.

**Signature (conceptual):**

```text
def get_partition_path_from_record(
    record: dict,
    partition_date_field: str,
    partition_date_format: str,
    fallback_date: datetime,
) -> str
```

- **Inputs:**  
  - `record`: RECORD message payload (dict).  
  - `partition_date_field`: Config value (field name in record).  
  - `partition_date_format`: strftime format string (e.g. `year=%Y/month=%m/day=%d`).  
  - `fallback_date`: Used when field is missing or unparseable (injected for tests).
- **Output:** Partition path string (e.g. `year=2024/month=03/day=11`).
- **Behaviour:**  
  - Read `record.get(partition_date_field)`.  
  - Parse as date/datetime (e.g. `datetime.fromisoformat`; one or two fallback formats).  
  - If missing or unparseable: use `fallback_date` formatted with `partition_date_format`.  
  - Return formatted string. No exception for bad data; fallback only.

**Placement:** Module-level in `sinks.py` or private method on GCSSink. Callable must receive `fallback_date` as argument (dependency injection for tests).

---

## GCSSink constructor and state

**Constructor:** `GCSSink(target, stream_name, schema, key_properties, *, time_fn=None, date_fn=None)` (or equivalent).

- **time_fn:** Optional callable `[[], float]` for Unix time (existing). Used for `{timestamp}` and deterministic tests.
- **date_fn:** Optional callable `[[], datetime]` for “today” (run date). Used for partition fallback and for any run-date token when partition-by-field is off. If not provided, use `datetime.today`. Enables deterministic tests for fallback and key names.

**State (when partition-by-field is on):**

- `_current_partition_path: Optional[str]` — Partition path for the current handle; `None` when closed/cleared.
- `_key_name: str` — Current key; cleared when partition changes or on rotation.
- `_gcs_write_handle` — Single open handle or None.
- Existing: `_records_written_in_current_file`, `_chunk_index`, `_time_fn`.

---

## Key building (GCSSink)

When partition-by-field is **off:** Existing behaviour. `key_name` property uses run date, `{date}`, `{timestamp}`, `{chunk_index}`; one key per sink (or per chunk when rotating).

When partition-by-field is **on:** Key is built per record at write time (no single cached `key_name` for the stream). Build uses:

- `stream` (stream name)
- `partition_date` (result of `get_partition_path_from_record` for this record)
- `timestamp` (from `time_fn` or time at build)
- `chunk_index` (when `max_records_per_file` > 0)

Template: `key_naming_convention` with tokens above. Prefix: same as today (`key_prefix` + template, normalized). After a partition change or rotation, the next key may reuse the same partition path but must get a new key (new file) via timestamp/chunk_index.

**Interface:** Internal method e.g. `_build_key_for_record(self, record: dict, partition_path: str) -> str` used from `process_record`. Receives partition path already resolved; uses `date_fn` only if needed for any run-date token when partition-by-field is off (existing path).

---

## process_record

**Signature (unchanged):** `process_record(self, record: dict, context: dict) -> None`

**Behaviour when `partition_date_field` is set:**

1. Resolve partition path: `get_partition_path_from_record(record, ..., date_fn())`.
2. If partition path != `_current_partition_path`: close handle, clear `_key_name`, set `_current_partition_path` to new path (or clear if design uses “no current” until next write). If chunking, reset `_chunk_index` on partition change (per architecture).
3. If chunking and record count >= max_records_per_file: rotate (close, clear key, increment chunk index, reset count); keep `_current_partition_path`.
4. Build key for this record: `_build_key_for_record(record, partition_path)`.
5. If handle is None, open handle for that key.
6. Write record to handle.
7. Increment `_records_written_in_current_file` if chunking.

**Behaviour when `partition_date_field` is unset:** Unchanged from current (existing key_name, single handle, existing rotation logic).

---

## Dependencies between interfaces

- Config schema → sink reads `partition_date_field`, `partition_date_format` via `self.config.get(...)`.
- Partition resolution is pure (record, config, fallback_date) → used by key building and by `process_record`.
- Key building depends on partition path, stream name, time_fn, chunk index, and config (key_naming_convention, key_prefix).
- Handle lifecycle depends on partition path equality and chunk rotation; no external API beyond existing GCS client and smart_open.
