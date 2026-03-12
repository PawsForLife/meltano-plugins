# Possible Solutions — target-gcs-partition-field-validation

## Requirement recap

When `partition_date_field` is set, validate before processing records: (1) the field exists in the stream schema (`schema.properties`), and (2) the property type is date-parseable (not null-only, not non-parseable types like integer/boolean).

## Option 1: Internal validation (recommended)

Implement validation inside target-gcs: in the sink (or a small helper), read `self.schema["properties"]`, check for the field and its type, and raise a clear error if invalid.

**Pros**: No new dependencies; full control over “date-parseable” rules; aligns with existing pattern (config + schema already in the sink); easy to unit test.  
**Cons**: We maintain the logic and any edge cases (e.g. `anyOf`/`oneOf` in schema).

**Schema availability and timing (Gemini / SDK verification)**:

- In Singer SDK, the target creates a sink when it has a stream name and schema (from the SCHEMA message). The base class `singer_sdk.sinks.Sink` receives `schema` in `__init__` and sets `self.schema = schema` and `self.original_schema = copy.deepcopy(schema)` (see `singer_sdk/sinks/core.py`). So **the schema is available as `self.schema` on the Sink after construction**; the SCHEMA message has already been processed by the target before the sink is created.
- **Validation in `__init__`** is appropriate: by the time `GCSSink.__init__` runs, `super().__init__` has been called, so `self.schema` is set. Running validation at the end of `__init__` (when `partition_date_field` is set) gives early, per-stream feedback.
- **`start_batch`** is not appropriate for RecordSink: in `singer_sdk.sinks.record.RecordSink`, `start_batch` is `@t.final` and does nothing. RecordSink does not use batching; the only place that has schema and runs once per stream is `__init__`.

**Conclusion**: Use **internal validation in the sink’s `__init__`** (after `super().__init__`), using `self.schema`.

## Option 2: External schema/validation library

Use a library (e.g. `jsonschema`, already a dependency of singer_sdk) to validate that a given property conforms to a “date-parseable” meta-schema.

**Pros**: Reuse of schema compilation/validation.  
**Cons**: We still must define “date-parseable” (which types/formats we allow) and map it to JSON Schema; the check is “does this property schema match our allowed pattern?” not “validate a record value”. So we’d use the library to interpret the schema (e.g. read `type`/`format`), not to validate records. That’s a thin wrapper; the core logic (allowed types, null-only rejection) remains in our code. Adds little over Option 1.

**Web note**: jsonschema validates *instance* data against a schema; format checkers (e.g. `date-time`) apply to values. For *schema*-level checks (e.g. “does this property have type string and format date-time?”), we still need to inspect `schema["properties"][field]` ourselves. So an “external” approach still reduces to reading the schema dict and applying our rules.

## Option 3: Defer to runtime (no upfront validation)

Do not validate at sink init; let record processing fail when an invalid value is encountered (e.g. in `get_partition_path_from_record`).

**Pros**: No new code paths.  
**Cons**: Fails later, possibly after some records are written; error may be less clear (e.g. KeyError or ParserError) and not mention stream name or config. Rejected per feature requirement (“validate before processing records”).

## Recommendation

**Option 1 — internal validation** in the sink’s `__init__`, using `self.schema` after `super().__init__`. Optionally factor the checks into a helper (e.g. `validate_partition_date_field_schema(stream_name, field_name, schema)`) for clarity and tests. No new external dependencies; schema and timing behaviour are as above.
