# Impacted Systems — split-path-filename

## Summary

The feature removes `key_naming_convention` config, splits path and filename into constants, uses timestamp-only chunking, and simplifies the path pattern hierarchy. The following existing systems are impacted.

---

## Modules

| Module | Impact |
|--------|--------|
| `target_gcs/constants.py` | Replace `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE` with `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`. Keep `DEFAULT_PARTITION_DATE_FORMAT` (used by helpers). |
| `target_gcs/target.py` | Remove `key_naming_convention` from `config_jsonschema`. |
| `target_gcs/sinks.py` | No direct use of `key_naming_convention`; delegates to path patterns. Pattern constructors receive config; patterns will stop reading `key_naming_convention`. |
| `target_gcs/paths/base.py` | Remove `key_template` property; add `filename_for_current_file() -> str`, `full_key(path, filename) -> str`; remove `get_chunk_format_map`; remove `_chunk_index`; chunking uses timestamp only. |
| `target_gcs/paths/simple.py` | Path from constants; use `filename_for_current_file`, `full_key`; remove `key_template`, `_build_key`; stop importing `DEFAULT_KEY_NAMING_CONVENTION`. |
| `target_gcs/paths/dated.py` | Path from constants; same flow as SimplePath; stop importing `DEFAULT_KEY_NAMING_CONVENTION_HIVE`. |
| `target_gcs/paths/partitioned.py` | Path from constants via `path_for_record(record)`; use `hive_path(record)`; remove `get_partition_path_from_schema_and_record` usage for key building; remove `key_template`, `record_path`; use `filename_for_current_file`, `full_key`. |
| `target_gcs/paths/__init__.py` | Remove exports of `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`; add exports for new constants if needed. |
| `target_gcs/helpers/partition_path.py` | May be removed or reduced: `get_partition_path_from_schema_and_record` is replaced by `hive_path(record)` in PartitionedPath. DatedPath uses extraction date directly. |

---

## Interfaces

| Interface | Change |
|-----------|--------|
| `BasePathPattern.key_template` | **Removed.** Path and filename come from constants. |
| `BasePathPattern.get_chunk_format_map()` | **Removed.** Replaced by `filename_for_current_file()` (timestamp-only). |
| `BasePathPattern._chunk_index` | **Removed.** Chunking uses timestamp only. |
| `BasePathPattern.filename_for_current_file()` | **Added.** Returns `{timestamp}.jsonl`. |
| `BasePathPattern.full_key(path, filename)` | **Added.** Joins path and filename, applies key_prefix. |
| Config schema `key_naming_convention` | **Removed.** |

---

## Functionality

| Area | Change |
|------|--------|
| Key generation | Path from constants; filename = `{timestamp}.jsonl`; no `chunk_index`. |
| Chunking | Timestamp-only; assume ≥1 second between chunks. |
| Partition path | PartitionedPath uses `hive_path(record)` from `_partitioned`; DatedPath uses extraction date formatted. |
| Config surface | `key_naming_convention`, `date_format` (for `{date}`) no longer used for key building. |

---

## External Artifacts

| Artifact | Change |
|----------|--------|
| `loaders/target-gcs/meltano.yml` | Remove `key_naming_convention` from settings and config example. |
| `loaders/target-gcs/README.md` | Remove `key_naming_convention` from config table; update Hive section; remove chunk_index and date_format references for key building. |
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Update config schema, key tokens, and path pattern descriptions. |

---

## Tests

| Test File | Impact |
|-----------|--------|
| `tests/unit/paths/test_base.py` | Add tests for `filename_for_current_file`, `full_key`; remove `key_template`, `get_chunk_format_map`, `chunk_index` tests. |
| `tests/unit/paths/test_simple.py` | Path from constants; filename = timestamp.jsonl; remove key_naming_convention tests. |
| `tests/unit/paths/test_dated.py` | Same as SimplePath. |
| `tests/unit/paths/test_partitioned.py` | Path from `path_for_record`; use `hive_path(record)`; remove `get_partition_path_from_schema_and_record` usage for key; partition change tests. |
| `tests/unit/test_sinks.py` | Remove `key_naming_convention` tests; assert key shape from constants. |
| Config schema tests | Remove `key_naming_convention` validation. |

---

## Dependencies

- `target_gcs.helpers.partition_path`: `get_partition_path_from_schema_and_record`; `DEFAULT_PARTITION_DATE_FORMAT` (imported from constants). PartitionedPath uses `hive_path(record)` from `_partitioned`; DatedPath uses extraction date. `get_partition_path_from_schema_and_record` may be removed if PartitionedPath fully migrates to `hive_path`; DatedPath does not need it.
- `target_gcs.paths._partitioned`: `get_hive_path_generator`; `date_as_partition`, `string_as_partition`; `is_date_field`. PartitionedPath already uses these; `get_partition_path_from_schema_and_record` is used for partition change detection. Feature spec: use `hive_path(record)` for path; partition change = compare `hive_path(record)` outputs.
