# Split Path and Filename Logic for target-gcs

## Background

The target-gcs loader currently uses `key_naming_convention` config to control path and filename format. This adds complexity and configuration surface. The goal is to simplify by:

- Removing `key_naming_convention` config entirely
- Using fixed defaults with path and filename/extension split in constants
- Keeping `key_prefix` for user-controlled prefix
- Using timestamp-only chunking (assume 1+ second between chunks; no `chunk_index`)

Greenfields project—no backwards compatibility required.

## This Task

### Fixed Path Formats (Constants)

| Pattern         | Full format                                           | Path part              | Filename            |
| --------------- | ----------------------------------------------------- | ---------------------- | ------------------- |
| SimplePath      | `{stream}/{date}/{timestamp}.jsonl`                   | `{stream}/{date}`      | `{timestamp}.jsonl` |
| DatedPath       | `{stream}/{hive:current_date}/{timestamp}.jsonl`      | `{stream}/{hive_path}` | `{timestamp}.jsonl` |
| PartitionedPath | `{stream}/{hive:*partition_fields}/{timestamp}.jsonl` | `{stream}/{hive_path}` | `{timestamp}.jsonl` |

**hive:** indicates hive partitioning (year=YYYY/month=MM/day=DD for dates; field=value for literals). For DatedPath, `hive_path` = extraction_date formatted. For PartitionedPath, `hive_path` = partition fields from record via `hive_path(record)`.

**Constants structure:** Split path template from filename template in `constants.py`:

```python
PATH_SIMPLE = "{stream}/{date}"
PATH_DATED = "{stream}/{hive_path}"
PATH_PARTITIONED = "{stream}/{hive_path}"
FILENAME_TEMPLATE = "{timestamp}.jsonl"
```

### Changes Required

1. **Constants**: Add `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; remove `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.
2. **Remove key_naming_convention**: From config (target.py, meltano.yml, README), path patterns; remove `key_template` property.
3. **BasePathPattern**: Add `filename_for_current_file() -> str`, `full_key(path, filename) -> str`; remove `get_chunk_format_map`; chunking uses timestamp only; remove `_chunk_index`.
4. **SimplePath**: Path at init from constants; process_record uses `filename_for_current_file`, `full_key`.
5. **DatedPath**: Path at init from constants; same process_record flow.
6. **PartitionedPath**: `path_for_record(record)` from constants; process_record: partition change detection, maybe_rotate_if_at_limit, filename, full_key.
7. **Removals**: `key_naming_convention`, `key_template`, `split_key_template`, `get_chunk_format_map`, `chunk_index`, static filename handling, `get_partition_path_from_schema_and_record`.

### Implementation Order

1. Update constants
2. Remove key_naming_convention from config and path patterns
3. Add `filename_for_current_file`, `full_key` to BasePathPattern; simplify/remove chunk_format_map
4. Remove `_chunk_index`; chunking uses timestamp only
5. SimplePath: path at init from constants
6. DatedPath: path at init from constants
7. PartitionedPath: path_for_record from constants; use hive_path(record)
8. Update tests and README

## Testing Needed

- **test_base.py**: `filename_for_current_file`, `full_key`, key_prefix, chunking via timestamp
- **test_simple.py**, **test_dated.py**: Path from constants; filename = timestamp.jsonl
- **test_partitioned.py**: Path comparison, partition change, chunking
- **test_sinks.py**: Remove key_naming_convention tests; assert key shape from constants
- Remove config schema tests for key_naming_convention
