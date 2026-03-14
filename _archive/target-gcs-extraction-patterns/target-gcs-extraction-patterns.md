# target-gcs-extraction-patterns — Archive Summary

## The request

**Background:** The target-gcs loader’s `GCSSink` (in `loaders/target-gcs/target_gcs/sinks.py`) handled all path logic in one place: branching on `hive_partitioned` and mixing (1) a simple single path per stream, (2) a Hive path by extraction/run date, and (3) a Hive path by stream schema `x-partition-fields`. That led to complex conditionals, key generation covering all cases, and harder testing.

**Goal:** Refactor so that `GCSSink` chooses one of three extraction patterns and delegates. Path-specific logic moves into the chosen pattern; `GCSSink` only selects and delegates (e.g. `process_record` → pattern’s `process_record`). The three patterns:

- **Simple:** Single path per stream (no Hive); optional chunking by `max_records_per_file`.
- **Dated:** Hive path from current (extraction) date only; no partition fields from schema.
- **Partitioned:** Hive path from schema `x-partition-fields` (record-driven; validated at init).

All patterns support extraction file size limits with default naming that adds `-{idx}` before the file extension when chunking (e.g. `my_stream_12345-0.jsonl`, `my_stream_12345-1.jsonl`). No new user-facing config: selection uses existing `hive_partitioned` and stream schema; config file and catalog remain the source of truth.

**Testing needs:** TDD for each pattern (key generation, rotation, handle lifecycle); black-box assertions on keys, file count, and record distribution; regression kept via existing tests in `loaders/target-gcs/tests/`; optional minimal end-to-end sync per mode.

---

## Planned approach

**Chosen solution:** Internal implementation only. No external library provides Singer target GCS extraction patterns or the required key template and partition semantics (PyArrow HivePartitioning is for reading; gcspathlib is path manipulation only). A shared base in `target_gcs.paths.base` and three concrete pattern classes were implemented; `GCSSink` selects one and delegates.

**Architecture:**

- **GCSSink** (RecordSink): In `__init__`, applies selection rule from config + stream schema, instantiates one of SimplePath, DatedPath, or PartitionedPath, stores it as `_extraction_pattern`, and delegates `process_record`, close/drain, and `key_name` to it.
- **BasePathPattern** (`paths/base.py`): Abstract base holding config, stream/schema, injectable dependencies (`time_fn`, `date_fn`, `storage_client`), and shared helpers: `apply_key_prefix_and_normalize`, `get_effective_key_template`, `write_record_as_jsonl`, `maybe_rotate_if_at_limit`, `flush_and_close_handle`, `get_chunk_format_map`. Subclasses implement key building and handle lifecycle; base does not open GCS handles.
- **SimplePath, DatedPath, PartitionedPath:** Concrete patterns in `paths/simple.py`, `paths/dated.py`, `paths/partitioned.py`; each implements `process_record`, `close`, and exposes current key.

**Selection rule (no new config):** `hive_partitioned` false or unset → SimplePath; `hive_partitioned` true and schema has non-empty `x-partition-fields` → PartitionedPath; `hive_partitioned` true and no/empty `x-partition-fields` → DatedPath.

**Task breakdown (8 tasks):** (01) Create BasePathPattern ABC and key-prefix/template helpers, stubs for write/rotation/flush/chunk-format; (02) Implement base rotation at limit, `write_record_as_jsonl`, `flush_and_close_handle`, chunk format map; (03) Implement SimplePath; (04) Implement DatedPath; (05) Implement PartitionedPath; (06) Refactor GCSSink to select pattern and delegate; (07) Wire `paths/__init__.py` exports and verify target/sink imports; (08) Regression run, test fixes, and documentation (AI context, CHANGELOG, optional README note).

---

## What was implemented

All eight tasks were completed (per pipeline scratchpad and CHANGELOG).

- **Tasks 01–02:** `target_gcs.paths.base` with `BasePathPattern`: constructor and state, `DEFAULT_KEY_NAMING_CONVENTION` and `DEFAULT_KEY_NAMING_CONVENTION_HIVE`, `apply_key_prefix_and_normalize`, `get_effective_key_template`, then full `write_record_as_jsonl`, `maybe_rotate_if_at_limit`, `flush_and_close_handle`, and `get_chunk_format_map`. Tests in `test_paths_base.py`.
- **Task 03:** SimplePath in `paths/simple.py`: single path per stream, one handle, rotation at `max_records_per_file`, `-{idx}` in key when chunking; tests in `test_simple_path.py`.
- **Task 04:** DatedPath in `paths/dated.py`: partition path from extraction date only (`DEFAULT_PARTITION_DATE_FORMAT`), one handle per run, same rotate/write/close semantics; tests in `test_dated_path.py`.
- **Task 05:** PartitionedPath in `paths/partitioned.py`: partition path per record via `get_partition_path_from_schema_and_record`, `validate_partition_fields_schema` at init, handle lifecycle on partition change, ParserError propagated; tests in `test_partitioned_path.py`.
- **Task 06:** GCSSink refactored: pattern selection in `__init__`, `process_record` and close/drain delegated to `_extraction_pattern`; `key_name` (returns pattern’s `current_key`) and `storage_client` delegate to pattern; inlined key/handle logic removed; tests updated to patch path modules and assert via `key_name` and mock open.
- **Task 07:** `target_gcs.paths` exports BasePathPattern, SimplePath, DatedPath, PartitionedPath, PathType, and key-naming constants; import smoke test for sinks and paths public API; no behaviour change.
- **Task 08:** Full suite passing; key shapes and record counts preserved; AI context and CHANGELOG updated to describe GCSSink delegation to extraction patterns; behaviour and key shapes unchanged; no new required config or env vars.

Backward compatibility: same config and stream schema semantics; same key shapes for simple, dated, and partitioned runs; existing tests that cover key generation, chunking, and hive vs non-hive behaviour continue to pass or were updated to assert the same behaviour via the new structure.
