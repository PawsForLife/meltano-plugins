# Plan Overview — split-path-filename

## Purpose

Split path and filename logic for target-gcs by replacing config-driven `key_naming_convention` with fixed constants. Path and filename templates live in `constants.py`; path patterns use `str.format()` for token expansion. Chunking uses timestamp-only (no `chunk_index`). Greenfields—no backwards compatibility.

---

## Objectives

1. **Remove `key_naming_convention`** from config schema, meltano.yml, README, and path patterns.
2. **Introduce path and filename constants** (`PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`) in `constants.py`.
3. **Add `filename_for_current_file()` and `full_key(path, filename)`** to `BasePathPattern`; remove `key_template`, `get_chunk_format_map`, `_chunk_index`.
4. **Migrate path patterns** to build path from constants and compose keys via `full_key`.
5. **Use `hive_path(record)`** in PartitionedPath for path building; replace `get_partition_path_from_schema_and_record` for key generation.
6. **Fix pre-existing bug** in `_partitioned.date_as_partition` so it returns a value.

---

## Success Criteria

- Config has no `key_naming_convention`; key shape is fixed by constants.
- SimplePath, DatedPath, PartitionedPath produce keys matching the feature spec table.
- Chunking rotates on `max_records_per_file` using timestamp-only filenames (≥1 second between chunks assumed).
- All tests pass; no regressions; black-box style preserved.
- Ruff, MyPy, pytest pass from `loaders/target-gcs/`.

---

## Key Requirements

| Requirement | Detail |
|-------------|--------|
| Path formats | SimplePath: `{stream}/{date}`; DatedPath/PartitionedPath: `{stream}/{hive_path}` |
| Filename | `{timestamp}.jsonl` for all patterns |
| Chunking | Timestamp-only; no `chunk_index` |
| Partition path | DatedPath: extraction date via `DEFAULT_PARTITION_DATE_FORMAT`; PartitionedPath: `hive_path(record)` from `_partitioned` |
| Config | `key_prefix` retained; `key_naming_convention` removed |

---

## Constraints

- No external libraries for template expansion; use `str.format()`.
- Dependency injection for `time_fn` and `date_fn` preserved for deterministic tests.
- File length cap: 500 lines per `.cursor/rules/content_length.mdc`.

---

## Relationship to Existing Systems

- **target_gcs**: Core refactor; config schema, sinks, and path patterns change.
- **meltano.yml / README**: Config surface reduced; docs updated.
- **AI context**: `AI_CONTEXT_target-gcs.md` updated for new config and key tokens.
