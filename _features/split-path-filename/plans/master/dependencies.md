# Dependencies — split-path-filename

## External Dependencies

**None added.** The feature uses internal `str.format()` for template expansion. No new packages in `pyproject.toml`.

---

## Internal Dependencies

### Module Dependencies

| Consumer | Depends On |
|----------|------------|
| `paths/base.py` | `constants.FILENAME_TEMPLATE`, `helpers._json_default`, `orjson`, `google.cloud.storage.Client` |
| `paths/simple.py` | `constants.PATH_SIMPLE`, `paths.base.BasePathPattern` |
| `paths/dated.py` | `constants.PATH_DATED`, `constants.DEFAULT_PARTITION_DATE_FORMAT`, `paths.base.BasePathPattern` |
| `paths/partitioned.py` | `constants.PATH_PARTITIONED`, `paths._partitioned` (hive_path, get_hive_path_generator), `paths.base.BasePathPattern` |
| `sinks.py` | `paths` (SimplePath, DatedPath, PartitionedPath) |
| `target.py` | `sinks.GCSSink` |

---

### _partitioned Module

- `get_hive_path_generator(schema, partition_fields, ...)` → callable
- `hive_path(record)` (or equivalent) — used by PartitionedPath
- `date_as_partition`, `string_as_partition`, `is_date_field` — must return values correctly

---

### helpers/partition_path

- `get_partition_path_from_schema_and_record` — may be removed or deprecated if PartitionedPath fully uses `hive_path(record)`.
- `DEFAULT_PARTITION_DATE_FORMAT` — currently in constants; used by `_partitioned` and DatedPath. Keep single source in `constants.py`.

---

## System Requirements

- Python ≥3.12, <4.0 (per target-gcs pyproject.toml)
- Existing deps: singer-sdk, google-cloud-storage, smart-open, orjson, etc.

---

## Environment Setup

- `source .venv/bin/activate` from `loaders/target-gcs/`
- `uv sync` for deps
- No new env vars

---

## Configuration

- **Config file:** `key_naming_convention` removed. Retained: `bucket_name`, `key_prefix`, `max_records_per_file`, `hive_partitioned`, `date_format`.
- **State file:** Unchanged (Singer state).
- **Catalog:** Unchanged; `x-partition-fields` in stream schema for PartitionedPath.
