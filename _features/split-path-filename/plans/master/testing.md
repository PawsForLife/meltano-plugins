# Testing — split-path-filename

## Strategy

TDD: write failing tests before implementation. Black-box: assert on observable behaviour (returned keys, written payloads, raised exceptions), not call counts or log lines. Per `.cursor/rules/development_practices.mdc` and `AI_CONTEXT_PATTERNS.md`.

---

## Test Layout

Per `.cursor/CONVENTIONS.md` and development_practices:

- **Path:** `loaders/target-gcs/tests/unit/` mirrors source path.
- **Naming:** `test_{source-basename}.py` (e.g. `paths/simple.py` → `tests/unit/paths/test_simple.py`).
- **Scope:** Unit tests focus on single module; no integration concerns in unit files.

---

## Test Files and Cases

### tests/unit/paths/test_base.py

**Purpose:** Validate `filename_for_current_file`, `full_key`, key_prefix, chunking.

| Test | What | Why |
|------|------|-----|
| `test_filename_for_current_file_returns_timestamp_jsonl` | `filename_for_current_file()` returns `{ts}.jsonl` with integer timestamp | Core filename contract |
| `test_filename_for_current_file_uses_injected_time_fn` | With `time_fn=lambda: 12345`, filename contains `12345` | DI for deterministic tests |
| `test_full_key_joins_path_and_filename` | `full_key("a/b", "c.jsonl")` → normalized key with prefix | Key composition |
| `test_full_key_applies_key_prefix` | With `key_prefix="x/y"`, result starts with prefix | Prefix application |
| `test_maybe_rotate_resets_records_no_chunk_index` | After rotate, next filename has new timestamp; no chunk_index in key | Timestamp-only chunking |
| Remove | Tests for `key_template`, `get_chunk_format_map`, `chunk_index` | Interfaces removed |

---

### tests/unit/paths/test_simple.py

**Purpose:** Path from constants; filename = timestamp.jsonl.

| Test | What | Why |
|------|------|-----|
| `test_path_from_path_simple_constant` | Key matches `{stream}/{date}/{timestamp}.jsonl` | Path format |
| `test_filename_is_timestamp_jsonl` | Filename segment is `{timestamp}.jsonl` | Filename format |
| `test_uses_date_format_from_config` | With `date_format="%Y"`, path contains year only | Config integration |
| Remove | Tests for `key_naming_convention` | Config removed |

---

### tests/unit/paths/test_dated.py

**Purpose:** Path from constants; hive_path = extraction date.

| Test | What | Why |
|------|------|-----|
| `test_path_from_path_dated_constant` | Key matches `{stream}/{hive_path}/{timestamp}.jsonl` | Path format |
| `test_hive_path_is_extraction_date_formatted` | hive_path = `year=YYYY/month=MM/day=DD` | DatedPath semantics |
| Remove | Tests for `key_naming_convention` | Config removed |

---

### tests/unit/paths/test_partitioned.py

**Purpose:** Path from `path_for_record`; `hive_path(record)`; partition change; chunking.

| Test | What | Why |
|------|------|-----|
| `test_path_for_record_uses_hive_path_of_record` | `path_for_record(record)` returns path with hive_path from record | Path per record |
| `test_partition_change_closes_handle_and_resets` | On partition change, new file opened; record count reset | Partition change behaviour |
| `test_chunking_within_partition` | At max_records, rotate; new filename; same partition path | Chunking within partition |
| Remove | Tests using `get_partition_path_from_schema_and_record` for key | Replaced by hive_path |

---

### tests/unit/test_sinks.py

**Purpose:** Sink-level key shape; no key_naming_convention.

| Test | What | Why |
|------|------|-----|
| `test_key_shape_matches_constants` | Key format matches `{prefix}/{stream}/{path}/{timestamp}.jsonl` | End-to-end key shape |
| Remove | Tests for `key_naming_convention` config | Config removed |
| Remove | Config schema tests for `key_naming_convention` | Schema change |

---

### tests/unit/helpers/test_partition_path.py (if applicable)

**Purpose:** If `get_partition_path_from_schema_and_record` is retained for other uses, keep relevant tests. If removed, remove or archive tests.

---

### _partitioned Tests

**Purpose:** Fix `date_as_partition` return.

| Test | What | Why |
|------|------|-----|
| `test_date_as_partition_returns_formatted_string` | `date_as_partition(dt)` returns non-empty string | Pre-existing bug fix |

---

## Integration Tests

- **Thin:** Integration tests (e.g. `test_target.py`, `test_core.py`) wire sink to target; assert key shape and record delivery. Trust path pattern unit tests; do not re-validate path logic.
- **Config:** Assert `key_naming_convention` not in config schema.

---

## Fixtures and Helpers

- `build_sink(config=..., time_fn=..., date_fn=..., storage_client=...)` — existing; use for deterministic keys.
- Schema fixtures with `x-partition-fields` for PartitionedPath tests.

---

## Validation Steps

1. `uv run pytest` from `loaders/target-gcs/` — all pass.
2. `uv run ruff check .` — no violations.
3. `uv run mypy target_gcs` — no errors.
4. Manual: run target with sample config; verify key format in mock or real bucket.
