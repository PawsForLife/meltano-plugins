# Background

The feature requires two new optional config properties so users can enable partition-by-record-date: the record field name and the strftime format for the Hive path segment. The config schema is the interface contract for the target; it must be in place before the sink reads these keys. No other tasks depend on code behaviour from this task—only that the schema exists and validates.

**Dependencies:** None (Phase 1: Models & Interfaces).

**Plan reference:** `plans/master/interfaces.md` (Config schema), `plans/master/implementation.md` (target.py changes).

---

# This Task

- **File:** `loaders/target-gcs/gcs_target/target.py`
- Add to `config_jsonschema` (Singer SDK `th.PropertiesList`):
  - `partition_date_field`: `th.Property(..., th.StringType, required=False, description="Record property name for partition path (e.g. created_at, updated_at). When set, partition-by-field is enabled.")`
  - `partition_date_format`: `th.Property(..., th.StringType, required=False, description="strftime-style format for Hive path segment. Default in code: year=%%Y/month=%%m/day=%%d.")`
- Do not change `default_sink_class`, CLI, or other target logic.
- **Acceptance criteria:** Schema exposes both properties as optional string; a target instance with `config={"bucket_name": "b", "partition_date_field": "created_at"}` constructs without validation error.

---

# Testing Needed

- **Schema includes partition_date_field:** Assert `GCSTarget.config_jsonschema["properties"]` contains `partition_date_field`, type string, not required. **WHAT:** New option is exposed. **WHY:** Config contract.
- **Schema includes partition_date_format:** Same for `partition_date_format`. **WHAT:** Format option exposed. **WHY:** Config contract.
- **Config with new keys validates:** `GCSTarget(config={"bucket_name": "b", "partition_date_field": "created_at"})` (and with `partition_date_format` set) does not raise. **WHAT:** Target accepts new config. **WHY:** Backward compatibility and new usage.

Follow TDD: add tests in `loaders/target-gcs/tests/test_sinks.py` (or test_target.py if schema tests live there) first, then add schema properties so tests pass.
