# Feature request: Hive partitioning by record date field (target-gcs)

**Plugin:** target-gcs (loaders/target-gcs)  
**Variant:** PawsForLife/meltano-plugins (Pet Circle); aligns with Datateer/target-gcs structure  
**Status:** Request

---

## Background

The project uses **target-gcs** from PawsForLife/meltano-plugins to write Singer stream data to GCS as JSONL. Current key naming uses `key_naming_convention` with tokens `{stream}`, `{date}`, and `{timestamp}`. The `{date}` value is derived from **run time** (`datetime.today()`) and formatted via `date_format` (e.g. `year=%Y/month=%m/day=%d` for Hive-style paths). Object keys are therefore one per stream per run; there is no use of record payload when building the path.

BigQuery external tables, Spark, and other data lake tooling can discover partitions from Hive-style paths (`year=YYYY/month=MM/day=DD/`). When the **partition should reflect the record’s event or business date** (e.g. `created_at`, `updated_at`) rather than the extraction run date, the loader must derive the partition path from a configurable date field in each record.

**Current implementation (Datateer/PawsForLife target-gcs):** In `target_gcs/sinks.py`, `GCSSink` computes `key_name` once per stream; `date` is set with `datetime.today().strftime(...)`. There is no read of record content when building the key. One GCS object is written per stream per run; all records go to that single key.

---

## This Task

Add support for **hive partitioning by a configurable date field** in the record so that:

1. **Config:** A new optional setting (e.g. `partition_date_field`) specifies the record property to use for the partition path (e.g. `created_at`, `updated_at`). An optional format (e.g. `partition_date_format`) may control the Hive path segment (default Hive-style `year=YYYY/month=MM/day=DD`).

2. **Key construction:** When `partition_date_field` is set, the object key includes a partition path derived from **that record’s field** (parsed as date/datetime, then formatted). Records with different partition values may be written to different object keys (multiple files per stream per run).

3. **Behaviour:** The sink must route each record to the correct key: either by maintaining one write handle per distinct partition value seen (and building key from that partition), or by flushing and reopening when the partition value changes. Missing or invalid values in the partition field must be handled (e.g. fallback to run date, or a dedicated partition like `__unknown__`).

4. **Backward compatibility:** When `partition_date_field` is not set, behaviour remains as today: `{date}` from run time, one key per stream per run.

---

## Proposed direction (research summary)

- **Schema:** Add `partition_date_field` (optional string) and optionally `partition_date_format` (optional string; default Hive-style).
- **Key naming:** Introduce a token such as `{partition_date}` for use in `key_naming_convention` when partition-by-field is enabled. For each record, resolve the partition path from the configured field (parse ISO date/datetime or common formats), format it, and use it in the key. When the option is unset, `{partition_date}` may be treated as run date or omitted from supported tokens.
- **Handles:** The sink currently has a single `gcs_write_handle` per stream. Supporting multiple partition values requires either: (a) a dict of handles keyed by partition path, or (b) closing and reopening the handle when the partition value changes (and flushing before close). Option (a) allows concurrent writes to multiple keys; (b) keeps one active handle and rotates when partition changes.
- **Edge cases:** Records missing the field, or with unparseable values, must not crash the target; define a fallback (e.g. run date or a sentinel partition) and document it.

---

## Testing Needed

- **Unit:** Given a stream and config with `partition_date_field` set, records with different values in that field produce distinct object keys (or distinct partition path segments) in the expected Hive format. Records with missing/invalid field use the defined fallback.
- **Unit:** When `partition_date_field` is unset, key generation is unchanged (run-date based, one key per stream).
- **Integration:** Run a tap → target-gcs pipeline with `partition_date_field` set; list GCS objects and confirm multiple keys per stream when records have different dates in that field; confirm paths are Hive-style and usable by BigQuery or Spark partition discovery.
- **Regression:** Existing jobs without the new config produce the same key layout as before.
