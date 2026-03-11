# Background

The sink must read an optional `max_records_per_file` value from config. The target's `config_jsonschema` is the single source of truth for allowed config; adding the property here enables validation and makes the option available to the sink via `self.config.get("max_records_per_file", 0)`.

No other tasks depend on this; the sink implementation will depend on this schema.

# This Task

- **File:** `loaders/target-gcs/gcs_target/target.py`
- Add to `config_jsonschema` (within the existing `th.PropertiesList`):
  - `th.Property("max_records_per_file", th.IntegerType, required=False, description="Maximum records per GCS object; 0 or unset = no chunking.")`
- Do not change `default_sink_class` or any other target behaviour.
- **Acceptance criteria:** Config that includes `"max_records_per_file": 1000` validates; config without the key still validates; schema documents the property.

# Testing Needed

- Add or extend a test in `loaders/target-gcs/tests/test_sinks.py` (or `test_core.py` if schema tests live there) that:
  - Asserts `GCSTarget.config_jsonschema["properties"]` contains `max_records_per_file`.
  - Asserts the property is not required (or that config without it is valid).
  - Asserts the property type is integer (per Singer SDK schema shape).
- Follow black-box style: assert schema structure/contract, not implementation details. Add a brief docstring: WHAT (schema exposes max_records_per_file) and WHY (sink needs it for chunking).
