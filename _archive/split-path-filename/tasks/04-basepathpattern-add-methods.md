# 04 — BasePathPattern: Add Methods, Remove Chunk Index

## Background

BasePathPattern must provide `filename_for_current_file()` and `full_key(path, filename)` for path patterns to compose keys. Remove `key_template`, `get_chunk_format_map`, and `_chunk_index`; chunking uses timestamp only. Depends on tasks 01 (constants), 03 (config removed). Subclasses (SimplePath, DatedPath, PartitionedPath) will be updated in tasks 05–07.

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/paths/base.py`

**Implementation steps (TDD first):**

1. **Tests first** in `tests/unit/paths/test_base.py`:
   - `test_filename_for_current_file_returns_timestamp_jsonl`: With `time_fn=lambda: 12345`, assert `filename_for_current_file()` returns `"12345.jsonl"`.
   - `test_filename_for_current_file_uses_injected_time_fn`: Deterministic time_fn yields predictable filename.
   - `test_full_key_joins_path_and_filename`: `full_key("a/b", "c.jsonl")` returns normalized key (path + filename, prefix applied).
   - `test_full_key_applies_key_prefix`: With `key_prefix="x/y"`, result starts with prefix.
   - `test_maybe_rotate_resets_records_no_chunk_index`: After rotate at max_records, next `filename_for_current_file()` has new timestamp; no chunk_index in key.
   - Remove tests for `key_template`, `get_chunk_format_map`, `chunk_index`.

2. **Implementation:**
   - Add `filename_for_current_file(self) -> str`: `return FILENAME_TEMPLATE.format(timestamp=round(time_fn()))`.
   - Add `full_key(self, path: str, filename: str) -> str`: `return self.apply_key_prefix_and_normalize(f"{path}/{filename}")`.
   - Remove `key_template` abstract property (subclasses will be updated in 05–07; this task may require stubs or temporary overrides until then — see note below).
   - Remove `get_chunk_format_map()`.
   - Remove `_chunk_index`; in `maybe_rotate_if_at_limit()`, do not increment chunk index; only flush, close, reset `_records_written_in_current_file`; next `filename_for_current_file()` yields new timestamp.
   - Import `FILENAME_TEMPLATE` from `target_gcs.constants`.

**Note:** Removing `key_template` will break subclasses until 05–07. Options: (a) make `key_template` a concrete property returning a placeholder until subclasses migrate, or (b) update subclasses in same task. Per implementation order, BasePathPattern is done before SimplePath; subclasses must still implement `process_record`. The plan says "remove key_template" — subclasses currently use it. The cleanest approach: remove the abstract `key_template` and have subclasses stop using it; they will use `full_key` instead. Subclasses in 05–07 will be updated to not reference `key_template`. For this task, remove from base and provide minimal stubs in subclasses so tests pass (or defer subclass updates to 05–07 and accept that 04 leaves base ready; 05 will fix SimplePath, etc.). Per the plan, 04 is "BasePathPattern only" — so we remove from base. Subclasses will fail until 05–07. The workflow says "each task independently verifiable" — so we need base tests to pass. Base tests don't need subclasses. We can add a concrete subclass in the test file for testing base behaviour, or test via a minimal subclass. The test_base.py tests `filename_for_current_file` and `full_key` — those can be tested on a minimal concrete subclass of BasePathPattern that implements the abstract methods. So: create a test helper subclass in test_base.py that implements `key_template` (or we remove key_template and the subclass implements `process_record` and `close` as no-ops). Once key_template is removed, the subclass won't need it. So the subclass in tests just needs `process_record` and `close`. Good.

**Acceptance criteria:**
- `filename_for_current_file()` and `full_key()` work per interface.
- `maybe_rotate_if_at_limit` uses timestamp-only; no `_chunk_index`.
- `key_template`, `get_chunk_format_map` removed from base.
- BasePathPattern tests pass. Subclass tests may fail until 05–07.
