# Background

Users and operators need clear documentation of the new config options, the `{partition_date}` token, fallback behaviour, and how chunking interacts with partition-by-field. Sample config and optional Meltano settings make the feature discoverable and easy to try.

**Dependencies:** Implementation tasks 01–07 complete. Documentation reflects the implemented behaviour.

**Plan reference:** `plans/master/documentation.md` (README, Sample config).

---

# This Task

- **File:** `loaders/target-gcs/README.md`
  - Document `partition_date_field` and `partition_date_format`: purpose, strftime format, default Hive-style value, both optional.
  - Document `{partition_date}` token: available when `partition_date_field` is set; replaced with partition path per record (e.g. `year=YYYY/month=MM/day=DD`). Note `{date}` remains run-date when partition-by-field is used.
  - Document fallback: when record is missing the field or value is unparseable, partition path uses run date (formatted with `partition_date_format`). No crash.
  - Add minimal example: config and `key_naming_convention` using `{partition_date}` (e.g. `{stream}/export_date={partition_date}/{timestamp}.jsonl`).
  - Chunking: when both `max_records_per_file` and `partition_date_field` are set, rotation happens within the current partition (same partition path, new file via timestamp/chunk index).
- **File:** `loaders/target-gcs/sample.config.json` (optional but recommended): Add example with `partition_date_field` and optional `partition_date_format`, and sample `key_naming_convention` using `{partition_date}`.
- **File:** `loaders/target-gcs/meltano.yml` (optional): Add settings for `partition_date_field` and `partition_date_format` if Meltano UI/env configuration is desired.
- **Acceptance criteria:** README is concise and accurate; sample config (if updated) validates; docs do not contradict implementation.

---

# Testing Needed

- No automated tests for documentation. Manual review: README and sample config match implementation (config keys, token name, fallback behaviour). Per project rules: update documentation to reflect code; never update code to match documentation.
