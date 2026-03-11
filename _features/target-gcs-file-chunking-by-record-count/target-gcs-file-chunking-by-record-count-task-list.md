# Task List: target-gcs-file-chunking-by-record-count

**Feature:** File chunking by record count (target-gcs)  
**Plan:** `_features/target-gcs-file-chunking-by-record-count/plans/master/`  
**Tasks:** `_features/target-gcs-file-chunking-by-record-count/tasks/`

---

## Execution Order

Tasks are ordered for TDD: config/schema and tests before implementation; models and interfaces first, then core logic, then integration, then validation/docs.

| Priority | Task | Description |
|----------|------|-------------|
| 01 | [01-add-config-schema.md](tasks/01-add-config-schema.md) | Add `max_records_per_file` to `config_jsonschema` in target.py; test schema contract. |
| 02 | [02-tests-chunking-disabled.md](tasks/02-tests-chunking-disabled.md) | Add tests: chunking disabled → one key, one handle; key has no chunk_index when convention omits it. |
| 03 | [03-sink-state-and-time-injection.md](tasks/03-sink-state-and-time-injection.md) | Add sink state (`_records_written_in_current_file`, `_chunk_index`) and time injection for tests. |
| 04 | [04-tests-rotation-and-key-format.md](tasks/04-tests-rotation-and-key-format.md) | Add tests: rotation at threshold, key format with chunk_index, record integrity. |
| 05 | [05-key-computation-with-chunk-index.md](tasks/05-key-computation-with-chunk-index.md) | Extend `key_name` to include `chunk_index` in format map when chunking enabled. |
| 06 | [06-rotation-and-process-record.md](tasks/06-rotation-and-process-record.md) | Implement rotation and counter update in `process_record`. |
| 07 | [07-handle-flush-on-close.md](tasks/07-handle-flush-on-close.md) | Flush handle before close in rotation block when supported. |
| 08 | [08-documentation-and-sample-config.md](tasks/08-documentation-and-sample-config.md) | README, sample config, meltano.yml, inline docstrings and comments. |

---

## Dependencies

- **01** has no task dependencies.
- **02** depends on 01 (valid config with/without key).
- **03** depends on 01.
- **04** depends on 01, 02, 03 (tests run; they fail until 05–06).
- **05** depends on 01, 03.
- **06** depends on 03, 05.
- **07** depends on 06.
- **08** depends on 06 (feature complete).

---

## Interface Requirements

- **Config:** `max_records_per_file` (integer, optional); sink reads via `self.config.get("max_records_per_file", 0)`.
- **GCSSink:** New private state `_records_written_in_current_file`, `_chunk_index`; `key_name` includes `chunk_index` in format map when chunking on; `process_record` rotates before write when at limit, then writes and increments count.
- **Time:** Injectable or patchable for deterministic tests (see tasks 03 and 04).

---

## Development Practices

- TDD: tests added before or with implementation; each task specifies testing needed.
- Black-box tests: assert observable behaviour (keys, record counts, open/close), not call counts or logs.
- No new external dependencies; follow `@.cursor/rules/development_practices.mdc`.
