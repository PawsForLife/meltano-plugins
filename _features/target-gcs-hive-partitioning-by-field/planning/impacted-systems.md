# Impacted systems — Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**Scope:** target-gcs loader (loaders/target-gcs).

---

## Summary

Adding optional partition-by-field changes how the GCS sink builds object keys and manages write handles. Existing behaviour (one key per stream per run, or per chunk when `max_records_per_file` is set) remains when the new config is unset.

---

## Modules / files

| Location | Impact |
|----------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | **High.** `GCSSink` today has a single `key_name` and single `gcs_write_handle` per stream. Partition-by-field requires key (and optionally handle) to depend on the current record’s partition value. Affected: `key_name` (or equivalent key resolution), `gcs_write_handle` (or handle selection/creation), `process_record`, and any rotation/close logic (e.g. `_rotate_to_new_chunk`). |
| `loaders/target-gcs/gcs_target/target.py` | **Medium.** Config schema must expose the new options (e.g. `partition_date_field`, optional `partition_date_format`). No change to sink class binding. |
| `loaders/target-gcs/tests/test_sinks.py` | **Medium.** New tests for: key/partition derived from record field; fallback when field missing/invalid; no behaviour change when option unset. Existing key_name and handle tests remain valid; may need parametrization or new cases for partition-by-field. |
| `loaders/target-gcs/README.md` | **Low.** Document new config and tokens (e.g. `{partition_date}` or Hive path segment). |
| `loaders/target-gcs/meltano.yml` | **Low.** Add settings for the new options if Meltano users should configure them via UI/env. |
| `loaders/target-gcs/sample.config.json` | **Low.** Optional example with partition-by-field. |

---

## Interfaces / behaviour

- **Key naming:** Today `key_name` is computed once per sink (or recomputed after chunk rotation) from `key_naming_convention` with tokens `{stream}`, `{date}`, `{timestamp}`, `{chunk_index}`. With partition-by-field, the effective “date” (or a new token) must be derived from the record when the option is set; when unset, behaviour is unchanged.
- **Handle lifecycle:** Currently one handle per sink, opened on first write. With multiple partition values, the sink either maintains multiple handles (e.g. keyed by partition path), or closes and reopens (or opens a new file) when the partition changes. Choice is in possible-solutions.
- **process_record(record, context):** Must read the configured date field from `record`, parse it, format for Hive path, then resolve key and write. Invalid/missing field must use a defined fallback (e.g. run date or sentinel partition) and must not crash.
- **Chunking:** If both `max_records_per_file` and partition-by-field are set, rotation can be defined per partition (e.g. rotate within current partition) or globally; design in selected-solution.

---

## Backward compatibility

- When `partition_date_field` is not set: key naming and handle behaviour must match current implementation (run-date `{date}`, one key per stream per run, or per chunk when chunking is on).
- Existing configs and pipelines must not require new keys.
