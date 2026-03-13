# Architecture — split-path-filename

## System Design

The feature refactors key generation from config-driven templates to fixed constants. Data flow remains: GCSSink → BasePathPattern (or subclass) → GCS write handle. The change is internal to path construction and filename generation.

---

## Component Breakdown

### Constants (`target_gcs/constants.py`)

| Constant | Value | Used By |
|----------|-------|---------|
| `PATH_SIMPLE` | `"{stream}/{date}"` | SimplePath |
| `PATH_DATED` | `"{stream}/{hive_path}"` | DatedPath |
| `PATH_PARTITIONED` | `"{stream}/{hive_path}"` | PartitionedPath |
| `FILENAME_TEMPLATE` | `"{timestamp}.jsonl"` | All patterns via `filename_for_current_file()` |
| `DEFAULT_PARTITION_DATE_FORMAT` | `"year=%Y/month=%m/day=%d"` | DatedPath, `_partitioned` |

Removed: `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.

---

### BasePathPattern (`target_gcs/paths/base.py`)

**Responsibilities:**
- Key prefix application and normalization (`apply_key_prefix_and_normalize`)
- Filename generation (`filename_for_current_file()`)
- Full key composition (`full_key(path, filename)`)
- Write, rotation, flush/close

**Removed:** `key_template`, `get_chunk_format_map`, `_chunk_index`.

**Chunking:** On rotate, `flush_and_close_handle()`, reset `_records_written_in_current_file`; next `filename_for_current_file()` uses new timestamp. No `_chunk_index` increment.

---

### SimplePath (`target_gcs/paths/simple.py`)

- **Path:** At init, `PATH_SIMPLE.format(stream=..., date=...)`; store as `_path`.
- **process_record:** `maybe_rotate_if_at_limit()` → `filename_for_current_file()` → `full_key(_path, filename)` → open handle if needed → write record.

---

### DatedPath (`target_gcs/paths/dated.py`)

- **Path:** At init, `hive_path = _extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)`; `path = PATH_DATED.format(stream=..., hive_path=hive_path)`; store as `_path`.
- **process_record:** Same flow as SimplePath.

---

### PartitionedPath (`target_gcs/paths/partitioned.py`)

- **Path per record:** `path_for_record(record) -> str`: `hive_path = self.hive_path(record)`; return `PATH_PARTITIONED.format(stream=..., hive_path=hive_path)`.
- **Partition change:** Compare `path_for_record(record)` with `_current_partition_path`; on change, flush/close, set `_current_partition_path`, reset `_records_written_in_current_file`.
- **process_record:** Resolve path; handle partition change; `maybe_rotate_if_at_limit()`; `filename_for_current_file()`; `full_key(path_for_record(record), filename)`; open handle if needed; write record.

---

## Data Flow

```
GCSSink.process_record(record)
  → _extraction_pattern.process_record(record, context)
    → maybe_rotate_if_at_limit()
    → path = path_for_record(record) or _path  # per-pattern
    → filename = filename_for_current_file()
    → key = full_key(path, filename)
    → open handle if needed
    → write_record_as_jsonl(record)
```

---

## Design Patterns

- **Dependency injection:** `time_fn`, `date_fn` passed into patterns for deterministic tests (per `AI_CONTEXT_PATTERNS.md`).
- **Template method:** `BasePathPattern` provides shared helpers; subclasses implement `process_record` and `close`.
- **Single responsibility:** Constants define format; patterns compose path and filename.

---

## _partitioned Module

- `get_hive_path_generator(schema, ...)` → callable that returns Hive path for a record.
- `hive_path(record)` (or equivalent) used by PartitionedPath.
- **Pre-existing bug:** `date_as_partition` must `return date_value.strftime(...)`; fix during implementation.
