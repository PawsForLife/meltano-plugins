# Selected solution — Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**Scope:** target-gcs loader (loaders/target-gcs).

---

## Approach

**Internal implementation** within target-gcs. Handle strategy: **Option (c) — Partial chunk (new file per partition visit, no reopen).** One active handle; when partition value changes, close and clear; when partition “returns” to a prior value, create a new key (e.g. with timestamp or visit index) and open a new file. No dict of handles and no reopen of the same path.

---

## Config

- **partition_date_field** (optional string): Record property for partition path (e.g. `created_at`). When set, partition-by-field is on.
- **partition_date_format** (optional string): Hive path segment format; default e.g. `year=%Y/month=%m/day=%d`. Used to format the parsed date for the key.

Add to `GCSTarget.config_jsonschema` in `gcs_target/target.py`. Sink reads via `self.config.get("partition_date_field")`, `self.config.get("partition_date_format", default_hive_format)`.

---

## Key naming

- New token **`{partition_date}`** in `key_naming_convention`. When `partition_date_field` is set, resolve per record from that field (parsed and formatted). When unset, either omit the token from allowed set or treat as run date so existing templates keep working; prefer omitting so behaviour is explicit.
- Key is built at write time when partition-by-field is on (not a single cached `key_name`). Base template still uses `{stream}`, `{timestamp}`, `{chunk_index}` (if chunking); `{partition_date}` is the partition path segment (e.g. `year=2024/month=03/day=11`). `{date}` remains run-date when partition-by-field is off.

---

## Partition resolution (algorithm)

1. **Read field:** `value = record.get(partition_date_field)`.
2. **Parse:** Try parsing as date/datetime (e.g. `datetime.fromisoformat` for ISO; one fallback format such as `%Y-%m-%d`). If value is missing or unparseable → use **fallback**: run date `datetime.today()` or sentinel (e.g. `__unknown__`); document in README.
3. **Format:** Apply `partition_date_format` (default Hive-style) to get partition path string.
4. **Return:** That string is used in key construction for this record.

---

## Proposed functions / interfaces

- **`_get_partition_path_from_record(record: dict, config: dict, fallback_date: datetime) -> str`**  
  Returns partition path string for the record. Uses `config["partition_date_field"]` and `config["partition_date_format"]`. Parses record field; on failure uses `fallback_date` (or sentinel). Can live in `sinks.py` as a module-level or sink method; inject `datetime` for tests (dependency injection for non-determinism).

- **`_build_key_for_record(record: dict, ...) -> str`**  
  When partition-by-field is on: get partition path from record, build full key from convention (prefix + template with `stream`, `timestamp`, `partition_date`, and optionally `chunk_index`). When off: use existing `key_name` logic (run date). Sink holds current partition value and current key/handle; on partition change, close handle and clear; on next write, build new key (new file for same partition if we “return” to it).

- **GCSSink state when partition-by-field is on:**  
  `_current_partition_path: Optional[str]`, `_current_key_name: str`, `_gcs_write_handle`. In `process_record`: compute partition path for this record; if path != `_current_partition_path`, close handle, clear `_current_key_name` and set `_current_partition_path` to new path; build key (new key every time after a change, so “return” to same partition gets new file); open handle if needed; write record. Chunking (`max_records_per_file`) can apply per current file: when rotating, keep same partition path but new key (timestamp/chunk_index).

---

## How it fits together

1. **Target:** Adds `partition_date_field` and `partition_date_format` to config schema.
2. **Sink constructor:** No new deps; optional `time_fn` and config as today. When partition-by-field is on, init `_current_partition_path = None`, `_current_key_name = ""`.
3. **process_record:** If `partition_date_field` not set, behaviour unchanged (existing key_name + single handle; chunk rotation as today). If set: get partition path from record via `_get_partition_path_from_record`; if path != current, close handle and reset current key/partition; build key for this record (new key when partition “returns”); ensure handle open for that key; write record; if chunking, increment and maybe rotate (rotate = new key same partition, close/reopen).
4. **Drain/close:** Close the single open handle if any; no dict to iterate.
5. **Tests:** Unit tests for partition resolution (valid/missing/invalid field, fallback); key differs by partition; unset config leaves behaviour unchanged. Black-box: assert keys and written data, not call counts.

---

## Fallback behaviour

- Missing field or unparseable value → use run date (`datetime.today()`) formatted with same partition_date_format. Document in config description and README. Alternative: sentinel partition (e.g. `__unknown__`) if product prefers to quarantine bad rows.

---

## Interaction with chunking

- When both `max_records_per_file` and `partition_date_field` are set: rotate to a new file after N records **within the current partition** (same path, new key via timestamp/chunk_index). So: one active handle; key = f(stream, partition_path, timestamp, chunk_index); on partition change close and reset chunk index for the new partition; on rotation within same partition, close and open new key, increment chunk index.
