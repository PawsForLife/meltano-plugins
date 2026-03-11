# Master Plan — Testing: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**See:** [overview.md](overview.md), [implementation.md](implementation.md), [interfaces.md](interfaces.md)

---

## Test strategy (TDD)

- Write tests **before** or **alongside** implementation. Tests define expected behaviour; implementation satisfies them.
- **Black box:** Assert on observable outcomes (key strings, written data, config schema, raised exceptions). Do not assert on call counts, log lines, or internal method invocations.
- **Valid tests:** Each test must be able to fail (e.g. by changing the implementation or input).
- **Regression gate:** Any failing test not marked `@pytest.mark.xfail` or `@unittest.expectedFailure` is a regression and must be fixed before the task is complete.

---

## Test layout

- **Location:** `loaders/target-gcs/tests/`. Existing: `test_sinks.py`, `test_core.py`.
- **New or extended:** Add partition-by-field cases to `test_sinks.py` (or a dedicated `test_sinks_partition.py` if file grows). Use existing `build_sink(config=..., time_fn=..., date_fn=...)` pattern; extend helper to accept `date_fn` when added.

---

## Unit tests: partition resolution

**Target:** `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str`

- **Valid ISO date in field:** Record `{partition_date_field: "2024-03-11"}` with default Hive format → returns `year=2024/month=03/day=11`. **WHAT:** Parsed date is formatted correctly. **WHY:** Core behaviour for partition path.
- **Valid ISO datetime in field:** Record with `"2024-03-11T12:00:00"` → partition path uses date part in Hive format. **WHAT:** Datetime is parsed and formatted. **WHY:** Common API format.
- **Fallback format (e.g. %Y-%m-%d):** Record with `"2024-03-11"` and format that accepts it → correct path. **WHAT:** Fallback parsing works. **WHY:** Support non-ISO strings.
- **Missing field:** Record without the key → returns `fallback_date.strftime(partition_date_format)`. Use fixed `date_fn`/fallback_date in test. **WHAT:** Fallback when field absent. **WHY:** No crash; predictable path.
- **Invalid value:** Record with non-date string (e.g. `"not-a-date"`) → returns fallback path. **WHAT:** Unparseable value uses fallback. **WHY:** Robustness.
- **Custom partition_date_format:** Custom format (e.g. `day=%d/month=%m`) → output matches. **WHAT:** Configurable format is applied. **WHY:** Flexibility for different Hive layouts.

All tests inject `fallback_date` so results are deterministic. No reliance on `datetime.today()` in tests.

---

## Unit tests: config schema

- **Schema includes partition_date_field:** `GCSTarget.config_jsonschema["properties"]` has `partition_date_field`, type string, not required. **WHAT:** New option is exposed. **WHY:** Config contract.
- **Schema includes partition_date_format:** Same for `partition_date_format`. **WHAT:** Format option exposed. **WHY:** Config contract.
- **Config with new keys validates:** `GCSTarget(config={"bucket_name": "b", "partition_date_field": "created_at"})` does not raise. **WHAT:** Target accepts new config. **WHY:** Backward compatibility and new usage.

---

## Unit tests: key building and sink behaviour (partition-by-field on)

- **Key differs by partition value:** Build sink with `partition_date_field`, `key_naming_convention` containing `{partition_date}`. Process record with date A; then record with date B. Assert two distinct keys (or key paths) produced. Use `time_fn` and `date_fn` fixed so keys are deterministic. **WHAT:** Different partition values yield different keys. **WHY:** Core partition-by-field behaviour.
- **Key includes Hive-style partition path:** One record with known date; assert key contains substring like `year=YYYY/month=MM/day=DD`. **WHAT:** Key format is Hive-compatible. **WHY:** BigQuery/Spark discovery.
- **Fallback used when field missing:** Sink with partition_date_field; process record without that field; assert key contains fallback date (from injected date_fn). **WHAT:** Missing field does not crash; path uses fallback. **WHY:** Robustness.
- **Unset partition_date_field: key unchanged:** Sink without `partition_date_field`; assert key uses run date (e.g. from date_fn or today) and single key per stream semantics. Compare to existing tests (e.g. `test_key_name_includes_default_date_format_if_date_token_used`). **WHAT:** No behaviour change when option unset. **WHY:** Backward compatibility.
- **Chunking with partition: rotation within partition:** Sink with `partition_date_field` and `max_records_per_file=2`. Process three records with same partition value. Assert two keys (chunk 0 and chunk 1) with same partition path segment. **WHAT:** Rotation creates new key but same partition. **WHY:** Chunking interaction.
- **Partition change closes handle and new key on return:** Process record partition A, then B, then A again. Assert three keys (A, B, A') where A' is a new key (e.g. new timestamp), not reopening A. **WHAT:** Option (c) behaviour: no reopen; new file when partition returns. **WHY:** Handle strategy.

Assert on keys (and optionally on which keys were opened) via observable behaviour (e.g. key names passed to open, or written paths if mock captures them). Do not assert “close was called once.”

---

## Unit tests: backward compatibility

- **Existing key_name tests still pass:** All current tests in `test_sinks.py` that do not set `partition_date_field` continue to pass (run-date key, prefix, timestamp, chunk_index, etc.). **WHAT:** No regression when feature unused. **WHY:** Regression gate.
- **key_name when partition_date_field unset:** Same as today: single key per stream (or per chunk). **WHAT:** key_name property behaviour unchanged. **WHY:** Existing callers and tests.

---

## Integration tests (optional, if in scope)

- **Tap → target-gcs with partition_date_field:** Run pipeline with config containing `partition_date_field`; feed records with different dates in that field. List GCS keys (or use mock/stub that records keys); assert multiple keys per stream and Hive-style path segments. **WHAT:** End-to-end partition-by-field. **WHY:** Real-world usage.
- **Regression: no partition_date_field:** Pipeline without the new config; assert key layout unchanged (one key per stream per run or per chunk). **WHAT:** Existing pipelines unaffected. **WHY:** Backward compatibility.

---

## Fixtures and helpers

- **build_sink:** Extend to accept `date_fn: Optional[Callable[[], datetime]] = None` and pass to `GCSSink`. Use in partition tests for deterministic fallback and key names.
- **Fixed date_fn/time_fn:** e.g. `date_fn=lambda: datetime(2024, 3, 11)`, `time_fn=lambda: 12345.0` for reproducible keys and partition paths in assertions.

---

## Exception tests

- No new exceptions required for “invalid config” (schema validates). If any code path raises (e.g. invalid format string), add `pytest.raises(ExpectedException)` test documenting expected failure. **WHAT:** Exception type and message. **WHY:** Contract for error handling.
