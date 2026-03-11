# Master Plan — Implementation: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**See:** [overview.md](overview.md), [architecture.md](architecture.md), [interfaces.md](interfaces.md), [testing.md](testing.md)

---

## Implementation order

1. **Config and schema** — Add properties to target; no behaviour change.
2. **Partition resolution** — Pure function + tests (TDD); injectable fallback date.
3. **Sink: date_fn and partition state** — Extend constructor and state; key/handle logic still unchanged when option unset.
4. **Key building with partition_date** — When option set, build key per record; token `{partition_date}`.
5. **Handle lifecycle** — On partition change close/clear; on next write open new key; chunking within partition.
6. **Integration** — Wire partition resolution and key building into `process_record`; regression and integration tests.

Models and interfaces first: config schema and partition-resolution signature are defined in interfaces.md; tests for partition resolution and key behaviour are written before or alongside implementation (TDD).

---

## Files to create or modify

### 1. `loaders/target-gcs/gcs_target/target.py`

- **Change:** Add to `config_jsonschema`:
  - `partition_date_field`: `th.Property(..., th.StringType, required=False, description="...")`
  - `partition_date_format`: `th.Property(..., th.StringType, required=False, description="...")`
- **No change:** `default_sink_class`, CLI, or other logic.

### 2. `loaders/target-gcs/gcs_target/sinks.py`

- **Partition resolution:** Add function (e.g. `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str`). Parsing: try `datetime.fromisoformat`; on failure try one fallback format (e.g. `%Y-%m-%d`). On missing or unparseable, return `fallback_date.strftime(partition_date_format)`. Default format constant for Hive: `year=%Y/month=%m/day=%d`.
- **GCSSink.__init__:** Add optional `date_fn: Optional[Callable[[], datetime]] = None`. When partition-by-field is on, use for fallback in partition resolution. Store as `self._date_fn`.
- **GCSSink state:** When `config.get("partition_date_field")`: init `_current_partition_path: Optional[str] = None`. Existing `_key_name` cleared when partition changes (already cleared on rotation).
- **Key building:** When partition-by-field is on, do not use single `key_name` property for write path. Add `_build_key_for_record(self, record, partition_path: str) -> str` that builds from `key_prefix`, `key_naming_convention`, with format_map: `stream`, `partition_date`, `timestamp` (from time_fn or time), `chunk_index` (if chunking). Use same normalization (no `//`, no leading `/`).
- **key_name property:** When `partition_date_field` is set, either return a placeholder or delegate to a “current” key only when there is one; callers that need key per record use `_build_key_for_record`. When unset, keep existing logic (run date, single key).
- **process_record:**  
  - If `partition_date_field` not set: existing logic (chunk rotation, write to key_name/handle).  
  - If set: (1) get partition path via `get_partition_path_from_record(..., self._date_fn() if self._date_fn else datetime.today)`; (2) if path != _current_partition_path: call existing close/clear logic (like _rotate_to_new_chunk but also clear _current_partition_path and set to new path); (3) if chunking and count >= max: rotate (keep partition path); (4) key = _build_key_for_record(record, partition_path); (5) if no handle or key changed, close if needed and open new handle for key; (6) write record; (7) increment count if chunking.
- **Handle open:** When partition-by-field is on, opening uses the key from _build_key_for_record. Reuse existing smart_open pattern; client from `Client()`.
- **Drain/close:** No change; single handle closed when sink is closed.

### 3. `loaders/target-gcs/tests/test_sinks.py` (and any new test module)

- Add tests per [testing.md](testing.md): partition resolution (valid/missing/invalid), key differs by partition, unset config unchanged, chunking with partition, fallback uses date_fn. Use `build_sink(..., date_fn=...)` where needed.

### 4. `loaders/target-gcs/README.md`

- Document new config options, `{partition_date}` token, fallback behaviour, and Hive path format. See [documentation.md](documentation.md).

### 5. `loaders/target-gcs/meltano.yml` (optional)

- Add settings for `partition_date_field` and `partition_date_format` if Meltano UI/env configuration is desired.

### 6. `loaders/target-gcs/sample.config.json` (optional)

- Add example with `partition_date_field` and optional `partition_date_format`.

### 7. `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`

- Update key naming and config sections for partition-by-field. See [documentation.md](documentation.md).

---

## Code organization

- Partition resolution stays in `sinks.py` (module-level or private method). No new package or module unless file length approaches 500 lines (see content_length.mdc); then consider extracting partition logic to a small module under `gcs_target/`.
- All new logic is under `loaders/target-gcs/`; no changes to tap or shared libs.

---

## Dependency injection

- **time_fn:** Already present; used for `{timestamp}`. Keep for key building when partition-by-field is on.
- **date_fn:** New optional callable `() -> datetime`. Used when partition-by-field is on for fallback in `get_partition_path_from_record`. Also usable for run-date in key when partition-by-field is off (optional, for test determinism). Passed in constructor; default `None` → use `datetime.today` in resolution and existing key_name behaviour.

---

## Implementation dependencies

- Config schema must be in place before sink reads the new keys.
- Partition resolution function must exist and be tested before process_record uses it.
- Key building and handle lifecycle depend on partition resolution and on date_fn/time_fn. Tests for “key differs by partition” and “fallback” require date_fn and time_fn.

Recommended task order for decomposition: (1) config schema + tests that schema accepts new keys; (2) partition resolution function + unit tests; (3) sink date_fn and _build_key_for_record + tests; (4) process_record branch and handle lifecycle + tests; (5) docs and sample config.
