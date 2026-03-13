# Task 09 — Meltano and README

## Background

Users and Meltano need the new config and schema convention documented; the plugin definition must expose `hive_partitioned` and drop old partition settings. Depends on config (04) and sink behaviour (07) being done.

## This Task

- **File:** `loaders/target-gcs/meltano.yml`
  - Add setting `hive_partitioned` (boolean, default false). Remove partition_date_field and partition_date_format if present.
- **File:** `loaders/target-gcs/README.md`
  - Document hive_partitioned: when true, Hive-style partitioning from stream schema or current date.
  - Document x-partition-fields: array of property names on stream schema; order = path order; each field must be required and non-nullable; date-parseable → YEAR/MONTH/DAY segment, else literal folder; literal sanitization (e.g. slash replaced).
  - Note removal of partition_date_field and partition_date_format.
- **Optional (per plans/master/documentation.md):** Update `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` and `loaders/target-gcs/CHANGELOG.md` to reflect the feature after implementation.

## Testing Needed

- No new automated tests. Manual check: README and meltano.yml are consistent with config schema and behaviour.
