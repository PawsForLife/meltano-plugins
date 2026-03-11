# Background

When `partition_date_field` is set, the key must be built per record using the partition path from `get_partition_path_from_record`, plus stream, timestamp, and chunk_index. The new token `{partition_date}` is replaced with that partition path. Key building must not use a single cached `key_name` for the whole stream when partition-by-field is on. This task adds `_build_key_for_record` and the tests that define its behaviour.

**Dependencies:** Tasks 01, 03, 04 (config, partition resolution, date_fn and partition state).

**Plan reference:** `plans/master/interfaces.md` (Key building), `plans/master/implementation.md` (Key building, key_name property), `plans/master/testing.md` (Key building and sink behaviour).

---

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- Add internal method `_build_key_for_record(self, record: dict, partition_path: str) -> str` that builds the key from `key_prefix`, `key_naming_convention`, with format_map: `stream`, `partition_date` (= partition_path), `timestamp` (from `time_fn` or time), `chunk_index` (if chunking). Use same normalization as existing key logic (no `//`, no leading `/`). Only used when `partition_date_field` is set.
- **key_name property:** When `partition_date_field` is set, either return a placeholder or delegate to the current key only when there is one; callers that need key per record use `_build_key_for_record`. When unset, keep existing logic (run date, single key).
- **File:** `loaders/target-gcs/tests/test_sinks.py`
- Extend `build_sink` usage to pass `date_fn` and `time_fn` where needed for deterministic assertions.
- **Acceptance criteria:** Keys built for records with different partition values differ; key includes Hive-style segment when format is default; fallback when field missing uses date_fn(); when option unset, key behaviour unchanged (existing key_name tests pass).

---

# Testing Needed

- **Key differs by partition value:** Sink with `partition_date_field`, `key_naming_convention` containing `{partition_date}`; process record with date A, then date B (or assert keys from _build_key_for_record with two partition paths differ). Use fixed `time_fn` and `date_fn`. **WHAT:** Different partition values yield different keys. **WHY:** Core partition-by-field behaviour.
- **Key includes Hive-style partition path:** One record with known date; assert key contains substring like `year=YYYY/month=MM/day=DD`. **WHAT:** Key format is Hive-compatible. **WHY:** BigQuery/Spark discovery.
- **Fallback used when field missing:** Sink with partition_date_field; use fallback path (from date_fn) in _build_key_for_record or process_record; assert key contains fallback date. **WHAT:** Missing field does not crash; path uses fallback. **WHY:** Robustness.
- **Unset partition_date_field: key unchanged:** Sink without `partition_date_field`; assert key uses run date and single-key semantics. Compare to existing tests (e.g. `test_key_name_includes_default_date_format_if_date_token_used`). **WHAT:** No behaviour change when option unset. **WHY:** Backward compatibility.

Write tests first (TDD), then implement `_build_key_for_record` and key_name behaviour. Assert on key strings (observable outcome); do not assert on call counts or internal method invocations.
