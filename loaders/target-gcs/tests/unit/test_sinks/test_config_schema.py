"""Tests for target config JSON schema: properties, validation, and exclusions."""

from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_config_schema_excludes_key_naming_convention() -> None:
    """WHAT: Config schema must not expose key_naming_convention; key shape is fixed by internal constants.
    WHY: Regression guard for config removal (split-path-filename task 03)."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "key_naming_convention" not in properties


def test_config_schema_has_no_credentials_file() -> None:
    """Target config file schema must not accept credentials_file; auth uses ADC or GOOGLE_APPLICATION_CREDENTIALS only."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "credentials_file" not in properties


def test_config_schema_includes_max_records_per_file() -> None:
    """Schema exposes max_records_per_file so the sink can read it for record-count-based chunking; config is validated by schema."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "max_records_per_file" in properties
    prop = properties["max_records_per_file"]
    type_val = prop.get("type")
    assert type_val == "integer" or (
        isinstance(type_val, list) and "integer" in type_val
    )
    required = schema.get("required") or []
    assert "max_records_per_file" not in required


def test_config_validates_with_max_records_per_file(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Config including max_records_per_file is valid; target instantiates without validation error."""
    config = {"bucket_name": "b", "max_records_per_file": 1000}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    assert target.config["max_records_per_file"] == 1000


def test_config_validates_without_max_records_per_file(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Config without max_records_per_file is valid; optional property may be omitted."""
    config = {"bucket_name": "b"}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    assert (
        target.config.get("max_records_per_file") is None
        or target.config.get("max_records_per_file") == 0
    )


def test_config_schema_includes_hive_partitioned() -> None:
    """Config schema exposes hive_partitioned (boolean, optional) so users can enable Hive-style partitioning from stream schema or current date."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "hive_partitioned" in properties
    prop = properties["hive_partitioned"]
    type_val = prop.get("type")
    assert type_val == "boolean" or (
        isinstance(type_val, list) and "boolean" in type_val
    )
    required = schema.get("required") or []
    assert "hive_partitioned" not in required
    assert prop.get("default") is False


def test_config_schema_omits_partition_date_field() -> None:
    """Config schema must not expose partition_date_field; replaced by hive_partitioned in schema-driven Hive partitioning."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "partition_date_field" not in properties


def test_config_schema_omits_partition_date_format() -> None:
    """Config schema must not expose partition_date_format; format is internal when using hive_partitioned."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "partition_date_format" not in properties


def test_config_validates_with_hive_partitioned(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Config with hive_partitioned true or false is valid; target instantiates and exposes the value (or default false)."""
    config_true = {"bucket_name": "b", "hive_partitioned": True}
    target_true = GCSTarget(config=config_true, storage_client=recording_storage_client)
    assert target_true.config["hive_partitioned"] is True
    config_false = {"bucket_name": "b", "hive_partitioned": False}
    target_false = GCSTarget(
        config=config_false, storage_client=recording_storage_client
    )
    assert target_false.config["hive_partitioned"] is False
    config_omitted = {"bucket_name": "b"}
    target_omitted = GCSTarget(
        config=config_omitted, storage_client=recording_storage_client
    )
    assert target_omitted.config.get("hive_partitioned") is False
