"""Tests for GCSSink Hive partition init validation: x-partition-fields and schema constraints."""

import pytest

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_sink_init_hive_partitioned_invalid_x_partition_fields_raises_value_error(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Sink init with hive_partitioned true and x-partition-fields containing a field not in schema properties raises ValueError.
    WHAT: Invalid x-partition-fields (e.g. 'missing' not in properties) is rejected at init. WHY: Fail fast so users get a clear config/schema error."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {"x-partition-fields": ["missing"], "properties": {}, "required": []}
    with pytest.raises(ValueError) as exc_info:
        target = GCSTarget(config=config, storage_client=recording_storage_client)
        GCSSink(
            target=target,
            stream_name="my_stream",
            schema=schema,
            key_properties=[],
            storage_client=recording_storage_client,
        )
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "missing" in msg
    assert "not in schema" in msg or "required" in msg.lower()


def test_hive_partitioned_set_field_missing_raises_value_error(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """hive_partitioned true with x-partition-fields listing a field missing from schema must raise ValueError at sink init."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {"x-partition-fields": ["dt"], "properties": {"id": {}}, "required": []}
    with pytest.raises(ValueError) as exc_info:
        target = GCSTarget(config=config, storage_client=recording_storage_client)
        GCSSink(
            target=target,
            stream_name="my_stream",
            schema=schema,
            key_properties=[],
            storage_client=recording_storage_client,
        )
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "dt" in msg


def test_hive_partitioned_set_field_null_only_raises_value_error(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """hive_partitioned true with null-only type for a partition field must raise ValueError so the field is not usable."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "null"}},
        "required": ["dt"],
    }
    with pytest.raises(ValueError) as exc_info:
        target = GCSTarget(config=config, storage_client=recording_storage_client)
        GCSSink(
            target=target,
            stream_name="my_stream",
            schema=schema,
            key_properties=[],
            storage_client=recording_storage_client,
        )
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "dt" in msg


def test_hive_partitioned_set_field_not_required_raises_value_error(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """hive_partitioned true with partition field not in required must raise ValueError so partition keys are always present."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": [],
    }
    with pytest.raises(ValueError) as exc_info:
        target = GCSTarget(config=config, storage_client=recording_storage_client)
        GCSSink(
            target=target,
            stream_name="my_stream",
            schema=schema,
            key_properties=[],
            storage_client=recording_storage_client,
        )
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "dt" in msg


def test_hive_partitioned_valid_schema_constructs_successfully(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """hive_partitioned true with valid x-partition-fields (field in properties, required, non-null) allows sink construction."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema=schema,
        key_properties=[],
        storage_client=recording_storage_client,
    )
    assert sink.stream_name == "my_stream"


def test_hive_partitioned_unset_constructs_successfully(
    sample_config: dict,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """When hive_partitioned is false or unset, sink must construct successfully with any schema; no regression when option is unset."""
    schema = {"properties": {"id": {}}}
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema=schema,
        key_properties=[],
        storage_client=recording_storage_client,
    )
    assert sink.stream_name == "my_stream"
