# Implementation Plan — Dependencies

## External Dependencies

- **No new packages**. Validation uses only the stream schema (dict) and Python stdlib. Optional: use `singer_sdk.helpers._typing` (e.g. `get_datelike_property_type`, `is_date_or_datetime_type`) if present and if they simplify “date-parseable” detection; this is an internal SDK dependency already used by the project.
- **Existing stack**: singer_sdk, target_gcs (google-cloud-storage, smart_open, orjson, etc.) unchanged. No new entries in `loaders/target-gcs/pyproject.toml` for this feature.

## Internal Dependencies

- **target_gcs.sinks**: Depends on the new helper (e.g. `target_gcs.helpers.partition_schema.validate_partition_date_field_schema` or `target_gcs.helpers.validate_partition_date_field_schema`). Sink must import the helper and call it from `GCSSink.__init__`.
- **target_gcs.helpers**: Provides the validation helper. May live in a new module (e.g. `partition_schema.py`) or in `partition_path.py`; in either case, export via `target_gcs/helpers/__init__.py` if the project uses it for public helpers.
- **target_gcs.target**: No change; target already passes schema into the sink constructor. No dependency from target to the validation helper.

## System and Environment

- **Python**: Unchanged (e.g. `requires-python = ">=3.12,<4.0"` per target-gcs `pyproject.toml`).
- **Environment**: Same as today; activate venv from `loaders/target-gcs/` and run `uv run pytest`, `uv run ruff`, `uv run mypy`. No new env vars or config.

## Configuration

- **Config file**: No new required or optional keys. `partition_date_field` remains an optional string in `GCSTarget.config_jsonschema`. Validation runs only when this key is set.
- **State file / Catalog**: No change. Validation does not read state or catalog; it uses only the stream schema passed to the sink. See `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` for config file, state file, and Catalog.
