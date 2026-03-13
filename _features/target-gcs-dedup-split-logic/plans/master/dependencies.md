# Dependencies: target-gcs-dedup-split-logic

## External Dependencies

No new external packages. Existing target-gcs dependencies unchanged: `singer-sdk`, `google-cloud-storage`, `google-api-python-client`, `smart-open[gcs]`, `orjson`, `requests`, etc. (see `loaders/target-gcs/pyproject.toml`).

## Internal Dependencies

- **sinks.py** imports from `target_gcs.helpers`: `_json_default`, `get_partition_path_from_schema_and_record`, `validate_partition_fields_schema`. After refactor, add `DEFAULT_PARTITION_DATE_FORMAT` from `.helpers.partition_path` (or `.helpers` if re-exported).
- **partition_schema.py** has no new internal imports; `_assert_field_required_and_non_null_type` is defined and used in the same module.

## System and Environment

- Python ≥3.12,<4.0 per target-gcs `pyproject.toml`. Venv and tooling per `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` (uv, ruff, mypy, pytest from plugin directory).

## Configuration

- No change to config file, state file, or Catalog usage. Target config (bucket_name, key_prefix, key_naming_convention, max_records_per_file, hive_partitioned, date_format) unchanged; see `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` for terminology.
