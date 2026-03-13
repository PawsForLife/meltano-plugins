# Interfaces — split-path-filename

## Public Interfaces

### Constants (`target_gcs/constants.py`)

```python
PATH_SIMPLE: str = "{stream}/{date}"
PATH_DATED: str = "{stream}/{hive_path}"
PATH_PARTITIONED: str = "{stream}/{hive_path}"
FILENAME_TEMPLATE: str = "{timestamp}.jsonl"
DEFAULT_PARTITION_DATE_FORMAT: str = "year=%Y/month=%m/day=%d"  # unchanged
```

---

### BasePathPattern

#### Added

```python
def filename_for_current_file(self) -> str:
    """Returns FILENAME_TEMPLATE.format(timestamp=round(time_fn()))."""

def full_key(self, path: str, filename: str) -> str:
    """Joins path and filename, applies key_prefix, normalizes slashes."""
```

#### Removed

- `key_template` (abstract property)
- `get_chunk_format_map() -> dict[str, Any]`
- `_chunk_index` (instance attribute)

---

### SimplePath

**Constructor:** Unchanged; receives `stream_name`, `config`, `time_fn`, `date_fn`, `storage_client`, `extraction_date`.

**Path:** Instance attribute `_path` set at init from `PATH_SIMPLE.format(stream=stream_name, date=date_str)` where `date_str = _extraction_date.strftime(date_format)`.

**process_record(record, context):** Same signature; uses `filename_for_current_file()`, `full_key(_path, filename)`.

---

### DatedPath

**Constructor:** Unchanged.

**Path:** Instance attribute `_path` set at init from `PATH_DATED.format(stream=stream_name, hive_path=hive_path)` where `hive_path = _extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)`.

**process_record(record, context):** Same as SimplePath.

---

### PartitionedPath

**Added:**

```python
def path_for_record(self, record: dict[str, Any]) -> str:
    """Returns PATH_PARTITIONED.format(stream=..., hive_path=hive_path(record))."""
```

**process_record(record, context):** Uses `path_for_record(record)` for path; partition change = compare with `_current_partition_path`; uses `filename_for_current_file()`, `full_key(path, filename)`.

---

### Config Schema (`target_gcs/target.py`)

**Removed:** `key_naming_convention` property from `config_jsonschema`.

**Retained:** `bucket_name`, `key_prefix`, `max_records_per_file`, `hive_partitioned`, `date_format` (for SimplePath `{date}` token).

---

### _partitioned Module

**date_as_partition:** Must return `date_value.strftime(...)`; current code may omit return (pre-existing bug).

**get_hive_path_generator / hive_path:** Used by PartitionedPath; output format `field=value` for literals, `year=.../month=.../day=...` for dates.

---

## Interface Contracts

| Method | Precondition | Postcondition |
|--------|--------------|---------------|
| `filename_for_current_file()` | `time_fn` or `time.time` available | Returns `{timestamp}.jsonl` with integer timestamp |
| `full_key(path, filename)` | `path`, `filename` non-empty strings | Returns normalized key with key_prefix applied |
| `path_for_record(record)` | PartitionedPath; record has partition fields | Returns `{stream}/{hive_path}` |

---

## Dependencies Between Interfaces

- `BasePathPattern.filename_for_current_file` uses `FILENAME_TEMPLATE` and `time_fn`.
- `BasePathPattern.full_key` uses `apply_key_prefix_and_normalize`.
- `PartitionedPath.path_for_record` uses `PATH_PARTITIONED`, `hive_path(record)` from `_partitioned`.
- `DatedPath` uses `PATH_DATED`, `DEFAULT_PARTITION_DATE_FORMAT`.
- `SimplePath` uses `PATH_SIMPLE`, `date_format` from config.
