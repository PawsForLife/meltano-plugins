# Pipeline Scratchpad

## Feature: target-gcs-file-chunking-by-record-count

- **Pipeline State:** Phase 3–4 complete; Phase 5–6 "Not started"
- **Task Completion Status:** Phase 1 research and planning docs done; Phase 2 master plan created; Phase 3 task list created.
- **Execution Order:** 01-add-config-schema.md, 02-tests-chunking-disabled.md, 03-sink-state-and-time-injection.md, 04-tests-rotation-and-key-format.md, 05-key-computation-with-chunk-index.md, 06-rotation-and-process-record.md, 07-handle-flush-on-close.md, 08-documentation-and-sample-config.md
- **Task count:** 8
- **Phase 1 output directory:** `_features/target-gcs-file-chunking-by-record-count/planning/`
- **Plan location:** `_features/target-gcs-file-chunking-by-record-count/plans/master/` (overview, architecture, interfaces, implementation, testing, dependencies, documentation).
- **Key findings:** Chunking affects only the target-gcs loader: `GCSSink` in `gcs_target/sinks.py` (record counter, key recomputation on rotation, close/reopen handle) and `GCSTarget` config in `target.py` (new optional `max_records_per_file`). No Singer protocol or tap changes. No suitable external library provides record-count-based GCS file rotation that fits RecordSink; BatchSink would be a larger refactor and not required.
- **Selected solution:** Internal implementation in `GCSSink`: add optional config `max_records_per_file`; per-stream state `_records_written_in_current_file` and `_chunk_index`; in `process_record`, when count reaches threshold, close handle, clear cached key, increment chunk index, reset counter so the next write opens a new file with a key that includes current timestamp and `{chunk_index}` for uniqueness. Key token `{chunk_index}` used only when chunking is enabled. Backward compatible when setting unset or 0.
- **Key decisions (Phase 2):**
  - Rotation runs **before** writing the record that would exceed the limit so that record is written to the new file; key recomputation uses current time and `chunk_index` in format_map when chunking is on.
  - Time used for key generation to be testable (injectable or patched in tests) so key/timestamp assertions are deterministic.
  - All chunking logic confined to `GCSSink`; config schema extended in `GCSTarget` only; TDD with tests in `test_sinks.py` asserting observable behaviour (keys, handle open/close, record counts), not call counts or logs.
- **Task plan created:** 03-sink-state-and-time-injection at plans/tasks/03-sink-state-and-time-injection.md
- **Task plan created:** 02-tests-chunking-disabled at plans/tasks/02-tests-chunking-disabled.md
- Task plan created: 04-tests-rotation-and-key-format at plans/tasks/04-tests-rotation-and-key-format.md
- **Task plan created:** 01-add-config-schema at plans/tasks/01-add-config-schema.md
- Task plan created: 05-key-computation-with-chunk-index at plans/tasks/05-key-computation-with-chunk-index.md
- Task plan created: 08-documentation-and-sample-config at plans/tasks/08-documentation-and-sample-config.md
- **Task plan created:** 07-handle-flush-on-close at plans/tasks/07-handle-flush-on-close.md
- Task plan created: 06-rotation-and-process-record at plans/tasks/06-rotation-and-process-record.md
- **Task 01-add-config-schema completed, tests passing.**
- Task 02-tests-chunking-disabled completed, tests passing.
- Task 03-sink-state-and-time-injection completed, tests passing.
- Task 04-tests-rotation-and-key-format completed, tests passing.
- Task 05-key-computation-with-chunk-index completed, tests passing.
- Task 06-rotation-and-process-record completed, tests passing.
