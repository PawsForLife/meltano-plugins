# Background

The behaviour change (literal segments as `field_name=value`) must be documented in code docstring (done in task 02), AI context, CHANGELOG, and optionally README. This task covers all documentation updates listed in the plan’s documentation.md. Depends on task 03 (code and tests are complete).

# This Task

- **Files to modify:**
  - `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`
  - `loaders/target-gcs/CHANGELOG.md`
  - `loaders/target-gcs/README.md` (optional)
- **Steps:**
  1. **AI context:** In `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`, under Public Interfaces for `get_partition_path_from_schema_and_record` and under Hive partitioning behaviour: state that literal segments are `field_name=value` (path-safe value); use example path e.g. `region=eu/year=2024/month=03/day=11`.
  2. **CHANGELOG:** In `loaders/target-gcs/CHANGELOG.md`, add an entry (e.g. under ### Changed): literal partition path segments are now Hive-standard `key=value` (e.g. `region=eu`, `country=UK`) instead of value-only; improves compatibility with Athena, Glue, BigQuery external tables, Spark. Note that existing object keys with value-only literal segments are not migrated; new writes use key=value. Follow project changelog format.
  3. **README (optional):** If the Hive partitioning section does not explicitly state that literal segments are always `key=value`, add one sentence to match the implementation.
- **Acceptance criteria:** Docs reflect current behaviour; CHANGELOG clearly describes the change and migration note; no updates to root CHANGELOG, glossary, or other AI context files unless specified in the plan.

# Testing Needed

- No automated tests for documentation. Verify by reading the updated sections for consistency with implementation and with `_features/hive-partition-key-value-paths/plans/master/documentation.md`.
