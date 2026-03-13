# Overview — Schema-driven Hive Partitioning

## Purpose

Enable target-gcs to drive Hive-style partitioning from **stream schema metadata** and a single **config flag**, instead of config-only partition field names. One tap with multiple streams can write to target-gcs; each stream’s partitioning is defined by its schema (`x-partition-fields`) and the global `hive_partitioned` flag.

## Objectives

- **Config**: Add `hive_partitioned: bool` (default `false`). When true, partition path is derived from stream schema and record (or current date when schema has no `x-partition-fields`). Remove config-driven `partition_date_field` and `partition_date_format` (backward compatibility not required).
- **Schema convention**: Stream schema may include `x-partition-fields: ["field1", "field2", ...]`. Array order defines path order. If absent when `hive_partitioned` is true, use current date for partition path.
- **Field rules**: Each field in `x-partition-fields` must exist in `schema["properties"]`, be in `schema["required"]`, and be non-nullable. Validation at sink init when `hive_partitioned` is true and `x-partition-fields` is present.
- **Field semantics**: Per field—date-parseable → one Hive date segment (`YEAR=.../MONTH=.../DAY=...`); otherwise → literal folder name. Path = concatenation of segments in field order.
- **Outcome**: Single tap, multiple streams, one target-gcs; config and schema drive partitioning without multiple tap variants.

## Success Criteria

- With `hive_partitioned: false` (default): no hive path; flat or existing non-hive behaviour unchanged.
- With `hive_partitioned: true` and no `x-partition-fields`: partition by current date (one segment).
- With `hive_partitioned: true` and `x-partition-fields`: path built from field values in order; date fields → YEAR/MONTH/DAY; non-date → folder name; validation rejects missing/optional/null-only partition fields.
- Tests are black-box (assert output path and behaviour); all tests pass; no new external dependencies.

## Key Requirements

- No new external packages; reuse `dateutil` and existing Hive date format.
- Literal segment values must be path-safe (no embedded `/`); sanitize or reject.
- Key template and handle lifecycle unchanged: `{partition_date}` (and `{hive}`) carry the full multi-segment path; partition change → close handle, clear state, new key on next write.

## Relationship to Existing Systems

- **target_gcs**: Target and sink remain the single consumer. Config schema gains `hive_partitioned`; partition logic switches from config field name to schema + record.
- **Helpers**: `partition_path.py` gains `get_partition_path_from_schema_and_record`; `partition_schema.py` gains `validate_partition_fields_schema`. Existing single-field path/validation can be internal or deprecated once call sites use the new API.
- **Meltano**: `meltano.yml` and README document the new setting and schema convention; no change to tap/target process boundary.

## Constraints

- Adhere to `@.cursor/rules/development_practices.mdc`: TDD, models for complex data, dependency injection for non-determinism (e.g. `date_fn` already used in sink).
- Adhere to `@.cursor/rules/content_length.mdc`: no plan or code file exceeds 500 lines.
- Follow existing patterns in `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` and `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`.
