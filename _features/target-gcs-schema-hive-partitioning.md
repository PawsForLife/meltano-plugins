# Background

target-gcs currently uses a config parameter to control partition field(s) and behaviour. We are the only consumer; backwards compatibility is not required. We want to simplify configuration and support a single tap with multiple streams all writing to target-gcs, with partitioning driven by schema metadata and a single boolean flag.

# This Task

- **Config**: Add `hive_partitioned: bool` (default `false`). When `true`, enable hive partitioning. No config-driven partition field name(s).
- **Schema extension**: Use `x-partition-fields: ["field1", "field2", ...]` on the stream schema. If present when `hive_partitioned` is true, use these fields (in order) to build the hive partition path; otherwise use current date for partition path.
- **Partition field rules**: Each field in `x-partition-fields` must be required and non-nullable in the schema.
- **Field semantics**:
  - If a field is parsable as a date (prefer schema format hint, fallback to parse check): use existing date hive structure (YEAR=.../MONTH=.../DAY=...).
  - Otherwise treat as enum: use the value as a literal folder name.
- **Path order**: Path reflects the order of fields in `x-partition-fields`:
  - `[my_enum, my_date]` → `my_enum_value/YEAR=.../MONTH=.../DAY=.../timestamp.yml`
  - `[my_date, my_enum]` → `YEAR=.../MONTH=.../DAY=.../my_enum_value/timestamp.yml`
- **Outcome**: One tap, multiple streams, one target-gcs; config and schema drive partitioning without multiple tap variants.

# Testing Needed

- Tests for `hive_partitioned: false` (default): no hive path; flat or existing non-hive behaviour.
- Tests for `hive_partitioned: true` without `x-partition-fields`: partition by current date.
- Tests for `hive_partitioned: true` with `x-partition-fields`: path built from field values in order; date fields → YEAR/MONTH/DAY; non-date → folder name.
- Tests that required/non-nullable validation is enforced for partition fields.
- Tests for multiple partition fields in different orders (enum then date, date then enum).
- Black-box style: assert output path and behaviour, not internal calls.
