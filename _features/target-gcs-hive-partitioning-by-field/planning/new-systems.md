# New systems — Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**Scope:** target-gcs loader (loaders/target-gcs).

---

## Summary

New behaviour is confined to the target-gcs package: config options, partition resolution from records, and (depending on chosen approach) handle management for multiple partition paths. No new top-level modules are required; additions are inside existing `gcs_target` and tests.

---

## New config (target)

- **partition_date_field** (optional string): Record property used for the partition path (e.g. `created_at`, `updated_at`). When set, partition-by-field is enabled.
- **partition_date_format** (optional string): Format for the Hive path segment. Default Hive-style (e.g. `year=%Y/month=%m/day=%d` or equivalent). When omitted, use a documented default compatible with BigQuery/Spark partition discovery.

Declared in `GCSTarget.config_jsonschema` and read in `GCSSink` via `self.config.get(...)`.

---

## New key token / path segment

- A token (e.g. `{partition_date}`) for use in `key_naming_convention` when partition-by-field is enabled. For each record, resolve from the configured field → parse as date/datetime → format with `partition_date_format` → substitute in key. When option is unset, `{partition_date}` may be treated as run date or omitted from supported tokens (backward compatibility).

---

## Partition resolution (new logic)

- **Input:** Record (dict), config (`partition_date_field`, `partition_date_format`).
- **Output:** Partition path string (e.g. `year=2024/month=03/day=11`) for use in key.
- **Parsing:** Support common formats (e.g. ISO date/datetime strings). Use a single parsing path (e.g. `datetime.fromisoformat` plus one or two fallbacks, or a small set of formats) to avoid dependency bloat. Validation: load into a clear contract (e.g. parsed date); if parsing fails, do not use for partition.
- **Fallback:** When the field is missing or unparseable, use a defined fallback: e.g. run date (`datetime.today()`) or a sentinel partition (e.g. `__unknown__`). Document in README and config description.

This can live in the sink module as a private helper or a small dedicated function used by the sink.

---

## Handle / file behaviour (depends on selected approach)

- **Option A — Dict of handles:** New structure (e.g. dict keyed by partition path) holding one GCS write handle per partition; create on first record for that partition, close on sink drain.
- **Option B — Close/reopen:** No new persistent structure; close current handle when partition value changes, clear key cache, reopen on next write for (possibly same or different) partition.
- **Option C — Partial chunk (new file per partition visit):** One “current” handle; when partition changes, close and clear; when partition equals a previously seen value, do not reopen—create a new key (e.g. with timestamp or chunk index) so each “visit” to a partition gets a new file. Yields more, smaller files; avoids reopen and handle-dict complexity.

See possible-solutions.md for comparison; selected-solution.md will specify which is implemented.

---

## Tests (new)

- Partition path derived from record field; multiple distinct partition values produce distinct keys (or path segments).
- Missing or invalid partition field uses fallback; no crash.
- `partition_date_field` unset: key generation unchanged (run-date based, one key per stream or per chunk).
- Integration (if in scope): tap → target-gcs with partition-by-field; list GCS keys and assert Hive-style paths and multiple keys per stream when records have different dates.

---

## Documentation

- README: describe new options, token, fallback behaviour, and Hive path format.
- AI context (e.g. `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`): update key naming and config sections to include partition-by-field.
