# Implementation Plan — Documentation

## Documentation to Create

- **None** for user-facing docs. The feature is a validation step; behaviour is “config with partition_date_field is validated at startup.” Existing target-gcs README and Meltano usage do not require a new section unless the team wants to document the error messages for troubleshooting.

## Documentation to Update

- **AI context**: After implementation, update `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` to mention that when `partition_date_field` is set, the sink validates at init that the field exists in the stream schema and has a date-parseable type; on failure a `ValueError` is raised with stream name, field name, and reason. Optionally add the helper name and location (e.g. `validate_partition_date_field_schema` in `target_gcs.helpers`).
- **CHANGELOG**: Add an entry under the next release (e.g. “Added validation for partition_date_field: when set, the sink now validates at startup that the field exists in the stream schema and has a date-parseable type; invalid config raises ValueError with a clear message.”). Location: repo root `CHANGELOG.md` and/or `loaders/target-gcs/CHANGELOG.md` if the project maintains a per-plugin changelog.

## Code Documentation

- **Helper**: Add a Google-style docstring to `validate_partition_date_field_schema` describing: purpose (validate partition_date_field against stream schema); args (stream_name, field_name, schema); return (None); raises (ValueError with message including stream name, field name, and one of: not in schema, null-only, non–date-parseable type). Keep concise.
- **Sink**: Add a short comment in `GCSSink.__init__` at the validation call site, e.g. “Validate partition_date_field against stream schema when set; raises ValueError if missing or not date-parseable.”
- **Tests**: Per project rules, each test must have a clear comment or docstring stating **what** is being tested and **why** (e.g. “Field missing from schema raises ValueError so users get a clear config error.”).

## User-Facing Documentation

- No new user guide or how-to unless the team decides to document “partition by field” and validation in a dedicated section. Existing docs that describe `partition_date_field` can optionally add one line: “If set, the target validates at startup that the field exists in the stream schema and has a date-parseable type.”

## Developer Documentation

- **Plan docs**: This set of plan documents in `_features/target-gcs-partition-field-validation/plans/master/` is the developer-facing specification. No separate dev doc is required beyond AI context and code comments.
