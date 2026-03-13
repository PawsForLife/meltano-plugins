# Possible Solutions — Schema-driven Hive Partitioning

Options: external libraries vs internal implementation.

## Requirement summary

- Read partition field list from stream schema (`x-partition-fields`).
- Validate each field: required, non-nullable.
- Per field: if date-parseable → Hive date segment (YEAR=.../MONTH=.../DAY=...); else → literal folder.
- Build path in field order; key template unchanged (`{stream}/{partition_date}/{timestamp}.{format}`).

## Option A: Internal implementation

- **Approach**: Extend existing `partition_path` and `partition_schema` helpers; add a single “path from schema + record” function and “validate partition fields” for list of names. Reuse current date parsing (dateutil) and Hive date format. No new dependencies.
- **Pros**: No new dependencies; full control over x-partition-fields semantics and error messages; aligns with existing single-field partition logic; easy to test and change.
- **Cons**: We own all edge cases (e.g. literal values containing `/`, timezone handling for dates).

## Option B: PyArrow HivePartitioning

- **Finding**: PyArrow’s `pyarrow.dataset.HivePartitioning` is for **parsing** existing directory paths into partition expressions (e.g. for reading datasets), not for **building** paths from record values. It does not take a record dict or schema x-partition-fields.
- **Conclusion**: Not a fit for “build path from schema + record”; we still need internal path construction. Could be used only if we wrote paths in a format PyArrow later parses (we already do: key=value segments).

## Option C: JSON Schema library for validation only

- **Approach**: Use `jsonschema` (or similar) to validate that each partition field is required and non-nullable by validating a minimal document or by walking schema["properties"] and schema["required"]. Validation logic is simple (field in properties, in required, type ≠ null-only); a library adds a dependency for a small, clear check.
- **Pros**: Standard validation if we later add more schema rules.
- **Cons**: Overkill for “field in list, required, non-null”; current codebase already does similar checks in `partition_schema.py` without jsonschema.

## Option D: External “partition path from record” library

- **Finding**: No common Python library that (a) reads Singer-style stream schema with x-partition-fields and (b) builds Hive partition paths from record dicts with date vs enum semantics. Spark/PyArrow focus on read-side partitioning or different config models.
- **Conclusion**: No drop-in library; path building stays in-house.

## Recommendation

- **Path building and field semantics**: Internal (Option A). Reuse dateutil and existing Hive date formatting; add a small builder that iterates `x-partition-fields` and appends segments (date or literal).
- **Validation**: Internal (Option A); extend existing `partition_schema` pattern to accept a list of field names and assert required + non-nullable. Keeps dependencies unchanged and behaviour explicit.
- **Optional hardening**: For literal segments, sanitize or reject values that contain `/` or other path-unsafe characters; document behaviour in README.
