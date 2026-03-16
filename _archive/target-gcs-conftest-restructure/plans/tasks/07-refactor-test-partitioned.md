# Task Plan: 07-refactor-test-partitioned

## Overview

This task refactors `loaders/target-gcs/tests/unit/paths/test_partitioned.py` to use shared conftest factory `build_partitioned_path` and test_helpers' `key_from_open_call` instead of local `build_partitioned_sink` and `_key_from_open_call`. It implements **Phase 4 (refactor path tests)** of the master implementation plan for the partitioned path module. All test names and assertion logic are preserved; only the source of the path builder and key helper changes. **Prerequisites:** Task 01 (test_helpers with `key_from_open_call`) and Task 02 (conftest with `build_partitioned_path`) must be complete.

**Scope:** Modify `test_partitioned.py` only. No new files; no changes to production code or other test files.

---

## Files to Create / Modify

| Action | Path | Description |
|--------|------|-------------|
| **Modify** | `loaders/target-gcs/tests/unit/paths/test_partitioned.py` | Remove local `build_partitioned_sink` and `_key_from_open_call`; add imports for `build_partitioned_path` from conftest and `key_from_open_call` from test_helpers; replace all builder and key-extractor usages; keep per-test patch of `target_gcs.paths.partitioned.smart_open.open` (or use conftest fixture if one exists). Preserve all test names and assertions. |

**No new files.** No other files are modified.

---

## Test Strategy

- **No new tests.** This task is a refactor; existing tests in `test_partitioned.py` are the regression gate.
- **TDD:** Not applicable; behaviour is unchanged. Run the test file and full target-gcs suite before and after refactor; all tests must pass with identical assertions and outcomes.
- **Test file path (unchanged):** `loaders/target-gcs/tests/unit/paths/test_partitioned.py` — one test file per source module (`target_gcs.paths.partitioned`); path under `tests/unit/paths/` mirrors source.
- **Black-box preserved:** Assertions remain on key segments, handle close/open behaviour (via keys), exception type, and observable behaviour only where they already exist. Do not add assertions on call counts or log output beyond what is already there.
- **Validation:** Run `pytest loaders/target-gcs/tests/unit/paths/test_partitioned.py -v` and then the full target-gcs suite. Every test must pass; no assertion changes; no new failures.

---

## Implementation Order

1. **Add imports (top of file)**  
   - Import `build_partitioned_path` from conftest. From `loaders/target-gcs/tests/unit/paths/test_partitioned.py`, conftest lives at `loaders/target-gcs/tests/conftest.py`, so use `from ...conftest import build_partitioned_path` (two levels up from `paths/` to `tests/`).  
   - Import `key_from_open_call` from test_helpers: `from ...test_helpers import key_from_open_call`.  
   - Keep existing imports: `datetime`, `typing`, `unittest.mock`, `pytest`, `dateutil.parser`, `PartitionedPath`.

2. **Define default schema/partition_fields for reuse (optional but recommended)**  
   - The current `build_partitioned_sink()` uses a default schema with `x-partition-fields`, `properties`, and `required`. Conftest's `build_partitioned_path(schema, partition_fields, config=None, ...)` requires schema and partition_fields. Either conftest exposes a default partitioned schema (and partition_fields) for tests, or the test file keeps a single module-level constant (e.g. `_DEFAULT_PARTITIONED_SCHEMA`) and derives `partition_fields = schema.get("x-partition-fields") or []` so tests that relied on the old default can call `build_partitioned_path(_DEFAULT_PARTITIONED_SCHEMA, partition_fields, ...)` without repeating the dict. Prefer one place (conftest or one local constant) for the default schema used in multiple tests.

3. **Remove local definitions**  
   - Delete the entire local function `build_partitioned_sink` (lines 19–51 in current file).  
   - Delete the entire local function `_key_from_open_call` (lines 53–56).

4. **Replace builder calls with build_partitioned_path**  
   - For each test that called `build_partitioned_sink(...)`, replace with `build_partitioned_path(schema, partition_fields, ...)` using the same logical arguments.  
   - Map old kwargs to conftest signature: `config` → `config`; `time_fn` → `time_fn`; `date_fn` → `date_fn`; `storage_client` → `storage_client`; `stream_name` → `stream_name` (via **kwargs if supported by conftest); `schema` → `schema` (first positional); `extraction_date` → `extraction_date` (via **kwargs). Partition_fields is second positional; derive from schema when tests used the old default schema (e.g. `schema.get("x-partition-fields") or []`).  
   - Where the old builder merged config with `{"bucket_name": "test-bucket", "hive_partitioned": True}`, pass equivalent config to `build_partitioned_path` (conftest merges with SAMPLE_CONFIG; ensure hive_partitioned and bucket_name are set where tests expect them, e.g. via config dict or conftest defaults).  
   - Preserve stream_name default `"my_stream"` where tests assert on it (e.g. `subject.stream_name == "my_stream"`); pass `stream_name="my_stream"` in kwargs if the conftest factory supports it.

5. **Replace _key_from_open_call with key_from_open_call**  
   - test_helpers' `key_from_open_call` expects the **positional-args tuple** (i.e. `mock_open.call_args[0]`).  
   - Replace every `_key_from_open_call(mock_open.call_args)` with `key_from_open_call(mock_open.call_args[0])`.  
   - Replace every `_key_from_open_call(c)` in a list comprehension (e.g. over `mock_open.call_args_list`) with `key_from_open_call(c[0])`.

6. **Patch strategy**  
   - Keep the existing per-test `patch("target_gcs.paths.partitioned.smart_open.open", ...)` context in each test that uses it. Do not introduce a new conftest fixture unless Task 02 already added a `patched_partitioned_open` (or similar) fixture; if it exists, use it and request it as a test parameter, otherwise retain local patch.

7. **Run tests and fix regressions**  
   - Run `pytest loaders/target-gcs/tests/unit/paths/test_partitioned.py -v`. Fix any import errors, signature mismatches (e.g. missing stream_name or extraction_date in conftest factory), or assertion failures so that all tests pass with unchanged behaviour.  
   - Run the full target-gcs test suite and confirm no regressions.

8. **Lint/format**  
   - Run the project linter/formatter on `test_partitioned.py`; fix any issues.

---

## Validation Steps

- [ ] No local definitions remain: `build_partitioned_sink` and `_key_from_open_call` are removed.
- [ ] Imports: `build_partitioned_path` comes from conftest; `key_from_open_call` comes from test_helpers.
- [ ] Every test that built a PartitionedPath now uses `build_partitioned_path(schema, partition_fields, ...)` with equivalent config, time_fn, date_fn, stream_name, and schema; default schema/partition_fields are provided from one place (conftest or a single local constant).
- [ ] All key assertions that used `_key_from_open_call(...)` now use `key_from_open_call(mock_open.call_args[0])` or `key_from_open_call(c[0])` for call_args_list.
- [ ] Patch target remains `target_gcs.paths.partitioned.smart_open.open`; either per-test patch or conftest fixture used consistently.
- [ ] `pytest loaders/target-gcs/tests/unit/paths/test_partitioned.py -v` passes with the same number of tests and no failure.
- [ ] Full target-gcs suite passes: e.g. `pytest loaders/target-gcs/tests/ -v`.
- [ ] Project lint/format checks pass for `test_partitioned.py`.

---

## Documentation Updates

- **None required.** No user-facing or AI context docs need to change for this task. Optional: if the test file has inline comments that refer to "local builder" or "local helper", update them to mention "conftest" or "test_helpers" where it improves clarity.

---

## Notes

- **Conftest factory signature (interfaces.md):** `build_partitioned_path(schema, partition_fields, config=None, time_fn=None, date_fn=None, storage_client=None, **kwargs)`. If conftest does not accept `stream_name` or `extraction_date` in **kwargs, the implementer must add them to conftest's `build_partitioned_path` (Task 02 scope) or pass them in a way that matches PartitionedPath.__init__ (stream_name, schema, config, partition_fields, time_fn, date_fn, storage_client, extraction_date).
- **Default schema:** The current test file's default schema includes `"x-partition-fields": ["region", "dt"]`, matching properties and required. Keeping a single `_DEFAULT_PARTITIONED_SCHEMA` in the test file (and deriving partition_fields from it) avoids duplication and keeps the refactor minimal; alternatively conftest may define this default for all path tests.
- **Regression:** Any failing test (other than explicitly xfail) must be fixed before the task is complete.
