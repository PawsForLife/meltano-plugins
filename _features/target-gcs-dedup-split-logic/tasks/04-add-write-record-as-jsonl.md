# Task 04: Add _write_record_as_jsonl and refactor record-processing methods

## Background

Both `_process_record_single_or_chunked` and `_process_record_hive_partitioned` perform the same record write: `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default)` and write to `self.gcs_write_handle`. This task extracts that into a single private method and refactors both call sites. Depends on tasks 01–03 being done so that sinks.py refactors are applied in order.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`:
  - Implement `_write_record_as_jsonl(self, record: dict) -> None`: write `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default)` to `self.gcs_write_handle`. Use the same `_json_default` as today (from helpers or local).
  - Refactor `_process_record_single_or_chunked` to call `self._write_record_as_jsonl(record)` instead of inline orjson.dumps + write.
  - Refactor `_process_record_hive_partitioned` to call `self._write_record_as_jsonl(record)` instead of inline orjson.dumps + write.
- Add a Google-style docstring for `_write_record_as_jsonl` (purpose, Args for `record`, no Returns).

**Acceptance criteria:** Both record-processing paths use the new method; written payloads and line endings are unchanged; no duplicated orjson.dumps + write logic.

## Testing Needed

- No new tests; existing tests for chunked and hive-partitioned record write already validate written content (black-box). Run full target-gcs test suite to confirm regression gate passes.
