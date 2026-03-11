# Archive: Hive partitioning by record date field (target-gcs)

**Feature:** target-gcs-hive-partitioning-by-field  
**Plugin:** target-gcs (loaders/target-gcs)

---

## The request

The target-gcs loader writes Singer stream data to GCS as JSONL. Key naming used `key_naming_convention` with tokens `{stream}`, `{date}`, and `{timestamp}`; `{date}` was derived from **run time** (`datetime.today()`), so one object key per stream per run. BigQuery external tables, Spark, and other data lake tooling discover partitions from Hive-style paths (`year=YYYY/month=MM/day=DD/`). When the **partition should reflect the record’s event or business date** (e.g. `created_at`, `updated_at`) rather than the extraction run date, the loader must derive the partition path from a configurable date field in each record.

**Goal:** Add optional **hive partitioning by a configurable date field** so that: (1) config exposes `partition_date_field` (and optional `partition_date_format`); (2) when set, the object key includes a partition path derived from **that record’s field** (parsed and formatted); (3) records with different partition values may be written to different keys; (4) missing or invalid values use a defined fallback (e.g. run date) without crashing; (5) when the option is unset, behaviour remains unchanged (run-date `{date}`, one key per stream per run).

**Testing needs:** Unit tests for partition resolution (valid ISO date/datetime, fallback format, missing/invalid field, custom format); key building (key differs by partition, Hive path in key, fallback when field missing, unset leaves behaviour unchanged); chunking with partition and partition-change handle lifecycle (option c: no reopen, new file when partition “returns”). Regression: all existing tests pass when option is unset. Optional integration: tap → target-gcs with partition-by-field; multiple keys per stream and Hive-style paths.

---

## Planned approach

**Chosen solution:** Internal implementation within target-gcs. **Handle strategy: Option (c) — Partial chunk (new file per partition visit, no reopen).** One active GCS write handle per sink; when partition value **changes**, close handle and clear current key/partition state; when partition value **returns**, do not reopen the old file—build a **new** key (e.g. new timestamp or chunk index) and open a new file. No dict of handles; no reopen of the same path.

**Config:** Optional `partition_date_field` (record property name, e.g. `created_at`) and optional `partition_date_format` (strftime for Hive path segment; default `year=%Y/month=%m/day=%d`). New key token **`{partition_date}`**: when partition-by-field is on, resolved per record from the configured field (parsed and formatted); when unset, token not used so behaviour stays explicit.

**Partition resolution:** Pure function `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date) -> str`. Read field from record; parse (e.g. `datetime.fromisoformat` plus fallback `%Y-%m-%d`); if missing or unparseable, use `fallback_date` formatted with `partition_date_format`. Stdlib only; `fallback_date` injectable for tests.

**Architecture:** Config schema in `GCSTarget` (target.py). Partition resolution (module-level or sink-used) and key building in `sinks.py`. GCSSink gains optional `date_fn`, `_current_partition_path` when option set, and `_build_key_for_record(record, partition_path)` when partition-by-field is on. Chunking (`max_records_per_file`) applies **within** the current partition (same path, new key via timestamp/chunk index on rotation). Drain closes the single open handle.

**Task breakdown (9 tasks):** (1) Add config schema (`partition_date_field`, `partition_date_format`). (2) TDD: unit tests for `get_partition_path_from_record`. (3) Implement partition resolution. (4) Add `date_fn` to GCSSink and `_current_partition_path` when option set; extend `build_sink` with `date_fn`. (5) Add `_build_key_for_record` and `{partition_date}` token; key_name behaviour when option set; TDD tests. (6) Integrate into `process_record`: resolve partition, on partition change close/clear and reset chunk index, chunk rotation within partition, build key, open handle, write; tests for chunking and partition A→B→A. (7) Regression and backward compatibility: full suite passes; explicit test that unset leaves key/behaviour unchanged. (8) README, sample.config.json, optional meltano.yml. (9) AI context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) and docstrings for new code.

---

## What was implemented

All 9 tasks were completed.

**01 — Config schema:** `partition_date_field` and `partition_date_format` added to `GCSTarget.config_jsonschema` in `gcs_target/target.py` as optional strings with descriptions. Schema and validation tests in test_sinks.py; target accepts config with new keys.

**02 — Partition resolution tests:** Unit tests for `get_partition_path_from_record`: valid ISO date, valid ISO datetime, fallback format, missing field (fallback_date), invalid value (fallback), custom partition_date_format. Fixed `fallback_date` for determinism; tests written first (TDD).

**03 — Partition resolution implementation:** `get_partition_path_from_record(record, partition_date_field, partition_date_format, fallback_date)` implemented in `sinks.py`; stdlib parsing (fromisoformat + fallback `%Y-%m-%d`); default Hive format constant; fallback on missing/unparseable; Google-style docstring. All task-02 tests pass; no new deps.

**04 — Sink date_fn and partition state:** Optional `date_fn: Optional[Callable[[], datetime]] = None` added to `GCSSink.__init__` and stored as `_date_fn`. When `partition_date_field` is set, `_current_partition_path: Optional[str] = None` initialised. `build_sink` in tests extended to accept and pass `date_fn`. Tests: build_sink accepts date_fn; sink has _current_partition_path when option set; existing tests still pass.

**05 — Key building with partition_date:** `_build_key_for_record(self, record, partition_path)` added; builds key from key_prefix and key_naming_convention with `stream`, `partition_date`, `timestamp`, `chunk_index` (if chunking); same normalization as existing key logic. key_name when partition-by-field on returns current key or placeholder. Tests: key differs by partition value; key includes Hive-style segment; fallback when field missing; unset partition_date_field leaves key behaviour unchanged.

**06 — Handle lifecycle and process_record integration:** When `partition_date_field` is set: resolve partition path per record; if path != _current_partition_path, close handle and clear _key_name and _current_partition_path, reset _chunk_index; if chunking and record count >= max, rotate (close, clear key, increment chunk index, keep partition path); build key via _build_key_for_record; open handle if None or key changed; write record; increment count if chunking. When partition “returns,” new key (new file). Reuse smart_open/Client(). Tests: chunking with same partition yields two keys (chunk 0 and 1) with same partition path; partition A then B then A yields three distinct keys (no reopen).

**07 — Regression and backward compatibility:** Full test suite run; regressions fixed. Explicit test that when `partition_date_field` is unset, key_name uses run date and single-key-per-stream (or per-chunk) behaviour unchanged. date_fn used in key_name when unset for deterministic tests.

**08 — Documentation and sample config:** README updated with config table for partition_date_field and partition_date_format; subsection on Hive partitioning by record date field (`{partition_date}` token, fallback behaviour, example key_naming_convention, chunking interaction). sample.config.json and meltano.yml updated with partition options and example key_naming_convention using `{partition_date}`.

**09 — AI context and docstrings:** `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` updated: config list (partition_date_field, partition_date_format), tokens list (`{partition_date}`), partition-by-field behaviour (one handle, close on change, new key on return, fallback), extension points. Docstrings verified/added for `get_partition_path_from_record`, GCSSink class, `_build_key_for_record`; target.py property descriptions verified.

**Outcome:** target-gcs supports optional Hive partitioning by a configurable record date field. When enabled, object keys include a partition path derived from the record (e.g. `year=YYYY/month=MM/day=DD`); multiple keys per stream per run when partition values differ; one active handle; on partition change close and clear; “return” to a partition creates a new file. Fallback for missing/invalid field is run date. Backward compatible when options are unset. CHANGELOG entry documents the feature and task outcomes.
