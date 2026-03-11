# Task List: target-gcs-hive-partitioning-by-field

**Feature:** Hive partitioning by record date field (target-gcs)  
**Plan:** `_features/target-gcs-hive-partitioning-by-field/plans/master/`  
**Tasks:** `_features/target-gcs-hive-partitioning-by-field/tasks/`

---

## High-level tasks and interdependence

| Phase | Task | Description | Depends on |
|-------|------|-------------|------------|
| 1 | 01-add-config-schema | Add `partition_date_field` and `partition_date_format` to target config schema | — |
| 2 | 02-partition-resolution-tests | TDD: unit tests for `get_partition_path_from_record` | — |
| 2 | 03-partition-resolution-implementation | Implement partition resolution (stdlib only; injectable fallback_date) | 02 |
| 2 | 04-sink-date-fn-and-partition-state | Add `date_fn` to GCSSink; add `_current_partition_path` when option set | 01, 03 |
| 2 | 05-key-building-with-partition-date | `_build_key_for_record` and `{partition_date}` token; TDD tests | 01, 03, 04 |
| 3 | 06-handle-lifecycle-and-process-record-integration | process_record branch: partition change close/clear; chunking within partition | 01–05 |
| 4 | 07-regression-and-backward-compatibility | All existing tests pass; explicit test when option unset | 01–06 |
| 4 | 08-documentation-readme-and-sample-config | README, sample.config.json, optional meltano.yml | 01–07 |
| 4 | 09-ai-context-and-docstrings | AI_CONTEXT_target-gcs.md, docstrings for new code | 01–07 |

---

## Interface requirements

- **Config (GCSTarget):** Optional `partition_date_field` (string), optional `partition_date_format` (string). Sink reads via `self.config.get(...)`.
- **Partition resolution:** Pure function `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str`. Used by GCSSink in process_record and key building.
- **GCSSink:** Optional `date_fn: Callable[[], datetime]` in constructor; `_current_partition_path: Optional[str]` when partition-by-field is on. Key building via `_build_key_for_record(record, partition_path)` when option set.
- **Key naming:** When partition-by-field on: tokens `stream`, `partition_date`, `timestamp`, `chunk_index` (if chunking). No dict of handles; one active handle; on partition change close and clear; next write gets new key (new file when partition "returns").

---

## Execution order

1. `01-add-config-schema.md`
2. `02-partition-resolution-tests.md`
3. `03-partition-resolution-implementation.md`
4. `04-sink-date-fn-and-partition-state.md`
5. `05-key-building-with-partition-date.md`
6. `06-handle-lifecycle-and-process-record-integration.md`
7. `07-regression-and-backward-compatibility.md`
8. `08-documentation-readme-and-sample-config.md`
9. `09-ai-context-and-docstrings.md`

TDD: tests are written first for partition resolution (02) and key building (05); implementation follows in 03 and 05/06. Models and interfaces first: config schema (01) and partition-resolution contract (02/03) before sink behaviour (04–06).
