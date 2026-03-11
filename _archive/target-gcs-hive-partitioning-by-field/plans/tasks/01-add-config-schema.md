# Task Plan: 01-add-config-schema

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Add optional config schema properties for partition-by-record-date.  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/interfaces.md](../master/interfaces.md), [../master/testing.md](../master/testing.md)

---

## 1. Overview

This task adds two optional config properties to the target’s JSON schema so users can enable hive partitioning by a record date field. No sink behaviour or CLI logic is changed; the sink will read these keys in later tasks. Success means the schema declares both properties as optional strings and a target instance with the new keys constructs without validation error.

**Scope:** Config contract only. No `default_sink_class`, CLI, or sink code changes.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/gcs_target/target.py` | Modify | Add two `th.Property` entries to `config_jsonschema`: `partition_date_field` and `partition_date_format` (both `th.StringType`, `required=False`, with descriptions from interfaces.md). |
| `loaders/target-gcs/tests/test_sinks.py` | Modify | Add three tests: schema includes `partition_date_field`, schema includes `partition_date_format`, and config with new keys validates (see Test Strategy). |

No new files. No changes to `sinks.py`, `meltano.yml`, README, or sample config (those are later tasks).

---

## 3. Test Strategy

Follow TDD: add tests first, then add schema so tests pass.

**Location:** `loaders/target-gcs/tests/test_sinks.py`. Reuse existing pattern: `schema = GCSTarget.config_jsonschema`, `properties = schema.get("properties") or {}`, assert on `properties["..."]` and `required`.

| Test | What | Why |
|------|------|-----|
| **Schema includes partition_date_field** | `config_jsonschema["properties"]` contains `partition_date_field`; type string (or list including `"string"`); not in `required`. | Config contract for record field name. |
| **Schema includes partition_date_format** | Same for `partition_date_format`: present, type string, not required. | Config contract for strftime format. |
| **Config with new keys validates** | `GCSTarget(config={"bucket_name": "b", "partition_date_field": "created_at"})` does not raise; optionally `GCSTarget(config={"bucket_name": "b", "partition_date_field": "x", "partition_date_format": "year=%Y/month=%m"})`. | Target accepts new config; backward compatibility and new usage. |

Assert on observable outcomes only (schema dict shape, target construction). No assertions on call counts or logs. Type check: allow `type` to be `"string"` or `["string"]` (SDK may emit either).

---

## 4. Implementation Order

1. **Add tests** in `test_sinks.py`:
   - `test_config_schema_includes_partition_date_field` — property exists, type string, not required.
   - `test_config_schema_includes_partition_date_format` — property exists, type string, not required.
   - `test_config_validates_with_partition_date_field` — `GCSTarget(config={"bucket_name": "b", "partition_date_field": "created_at"})` and optionally with `partition_date_format`; no exception; `target.config` contains the values.
2. **Run tests** — expect failures (properties missing).
3. **Add schema** in `target.py`: append to the `th.PropertiesList`:
   - `th.Property("partition_date_field", th.StringType, required=False, description="Record property name for partition path (e.g. created_at, updated_at). When set, partition-by-field is enabled.")`
   - `th.Property("partition_date_format", th.StringType, required=False, description="strftime-style format for Hive path segment. Default in code: year=%Y/month=%m/day=%d.")`
4. **Run tests** — all new and existing tests pass.
5. **Lint/format** per project rules (e.g. Ruff).

---

## 5. Validation Steps

- [ ] All three new tests pass.
- [ ] Existing tests in `test_sinks.py` (and full test suite for `loaders/target-gcs`) still pass — no regression.
- [ ] `GCSTarget(config={"bucket_name": "b", "partition_date_field": "created_at"})` runs without validation error in a quick manual check if desired.
- [ ] Linter/type checker passes for modified files.

---

## 6. Documentation Updates

**This task:** No README, AI context, or sample config changes. Documentation for the new options is planned in task 08 (documentation-readme-and-sample-config).

**Optional:** If the project tracks config schema in a separate doc, add the two new properties there; the task does not require it.
