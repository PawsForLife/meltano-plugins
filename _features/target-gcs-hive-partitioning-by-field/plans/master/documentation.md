# Master Plan — Documentation: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**See:** [overview.md](overview.md), [implementation.md](implementation.md)

---

## User-facing documentation

### README (`loaders/target-gcs/README.md`)

- **New config options:** Describe `partition_date_field` and `partition_date_format`: purpose, format (strftime), default Hive-style value, and that both are optional.
- **Key naming:** Document the `{partition_date}` token: available when `partition_date_field` is set; replaced with the partition path for each record (e.g. `year=YYYY/month=MM/day=DD`). Note that `{date}` remains run-date when partition-by-field is used.
- **Fallback behaviour:** When the record is missing the field or the value is unparseable, the partition path uses the run date (formatted with `partition_date_format`). No crash; document so users understand where “bad” rows land.
- **Example:** Minimal example config and `key_naming_convention` using `{partition_date}` (e.g. `{stream}/export_date={partition_date}/{timestamp}.jsonl`).
- **Chunking:** When both `max_records_per_file` and `partition_date_field` are set, rotation happens within the current partition (same partition path, new file via timestamp/chunk index).

Keep README concise; link to this plan or AI context for implementation details if needed.

---

## Code documentation

- **Partition resolution function:** Docstring: inputs (record, field name, format, fallback_date), output (partition path string), and fallback behaviour (missing/unparseable → fallback_date). Google style.
- **GCSSink:** Update class docstring to mention partition-by-field: when `partition_date_field` is set, key is derived per record from that field; one handle; on partition change close and next write gets new key (new file when partition “returns”).
- ** _build_key_for_record (or equivalent):** Docstring: when partition-by-field is on, builds key from stream, partition_date, timestamp, chunk_index; used by process_record.
- **Config schema (target.py):** Property descriptions for `partition_date_field` and `partition_date_format` in `th.Property(..., description="...")` so they appear in generated schema docs.

---

## AI context

### `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`

- **Config schema:** Add `partition_date_field` and `partition_date_format` to the config list; note optional and default Hive format.
- **Key naming:** Add `{partition_date}` to the tokens list; explain it is per-record when partition-by-field is on and not available when off.
- **Behaviour:** Short paragraph: partition-by-field uses one handle; on partition change close and clear; “return” to a partition creates a new key (new file); fallback for missing/invalid is run date.
- **Extension points:** Note that custom sinks can override partition resolution or key building if needed.

---

## Sample config

- **sample.config.json (optional):** Add an example block or comment showing `partition_date_field` and optional `partition_date_format` with a sample `key_naming_convention` using `{partition_date}`. Keeps docs and code in sync.

---

## Changelog

- **CHANGELOG.md (repo or plugin):** Add entry for the feature: hive partitioning by record date field; new config options and token; backward compatible when options unset.
