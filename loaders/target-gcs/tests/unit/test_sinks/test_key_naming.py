"""Tests for GCSSink key naming: pattern shape, prefix, time, and extraction date."""

import re
from datetime import datetime

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_public_api_imports_succeed() -> None:
    """WHAT: Public API imports for sinks and paths resolve without circular import or missing exports.
    WHY: Smoke test so from target_gcs.sinks import GCSSink and from target_gcs.paths import pattern classes remain valid."""
    from target_gcs.paths import (
        BasePathPattern,
        DatedPath,
        PartitionedPath,
        PathType,
        SimplePath,
    )

    assert GCSSink is not None
    assert issubclass(SimplePath, BasePathPattern)
    assert issubclass(DatedPath, BasePathPattern)
    assert issubclass(PartitionedPath, BasePathPattern)
    assert PathType is not None


def test_extraction_timestamp_is_unix_time(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Key name after first write matches stream/date/timestamp.jsonl pattern. WHAT: key_name reflects pattern current key. WHY: Regression for simple path key shape (split-path-filename)."""
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    subject = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    assert re.match(r"my_stream/\d{4}-\d{2}-\d{2}/\d+\.jsonl", subject.key_name)


def test_key_shape_matches_constants(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Key format matches {prefix}/{stream}/{path}/{timestamp}.jsonl for each pattern (SimplePath, DatedPath, PartitionedPath).
    WHAT: key_name structure aligns with PATH_SIMPLE, PATH_DATED, PATH_PARTITIONED and FILENAME_TEMPLATE constants.
    WHY: Regression guard that sink delegates to patterns and key shape is fixed by constants (no key_naming_convention)."""

    def time_fn() -> float:
        return 99999.0

    # SimplePath: stream/date/timestamp.jsonl
    config = {"bucket_name": "test-bucket", "hive_partitioned": False}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"id": 1}, {})
    assert re.match(r"my_stream/\d{4}-\d{2}-\d{2}/99999\.jsonl", sink.key_name), (
        "SimplePath key must match stream/date/timestamp.jsonl"
    )

    # DatedPath: stream/year=X/month=Y/day=Z/timestamp.jsonl
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"id": 1}, {})
    assert re.match(
        r"my_stream/year=\d+/month=\d+/day=\d+/99999\.jsonl", sink.key_name
    ), "DatedPath key must match stream/hive_path/timestamp.jsonl"

    # PartitionedPath: stream/field=value/.../timestamp.jsonl
    schema = {
        "x-partition-fields": ["r"],
        "properties": {"r": {"type": "string"}},
        "required": ["r"],
    }
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema=schema,
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"id": 1, "r": "x"}, {})
    assert re.match(r"my_stream/r=x/99999\.jsonl", sink.key_name), (
        "PartitionedPath key must match stream/hive_path/timestamp.jsonl"
    )


def test_key_name_includes_prefix_when_provided(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Key name includes key_prefix when provided. WHAT: key_name reflects prefix. WHY: Config key_prefix must appear in written key."""
    config = {"bucket_name": "test-bucket", "key_prefix": "asdf"}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    subject = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    assert re.match(r"asdf/my_stream", subject.key_name)


def test_key_name_does_not_start_with_slash(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Key name never starts with leading slash. WHAT: key_name is normalized. WHY: GCS key shape requirement."""
    config = {"bucket_name": "test-bucket", "key_prefix": "/asdf"}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    subject = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    assert not subject.key_name.startswith("/")


def test_key_name_uses_injectable_time_fn_when_provided(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Key name uses injectable time when time_fn is provided so tests can assert key content without flakiness.
    WHAT: key_name uses time_fn for extraction_timestamp when passed to GCSSink. WHY: deterministic key assertions in tests."""
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    subject = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    assert "12345" in subject.key_name


def test_sink_accepts_extraction_date_and_uses_it(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Sink stores and uses injectable extraction_date when provided. WHAT: extraction_date is injectable for run-date.
    WHY: Deterministic tests for partition fallback and key names."""
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    subject = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    assert subject._extraction_date is not None
    assert subject._extraction_date == fixed_date
