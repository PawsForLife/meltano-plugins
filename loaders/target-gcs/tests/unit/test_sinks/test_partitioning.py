"""Tests for GCSSink Hive partitioning key/path behaviour and handle lifecycle."""

from datetime import datetime

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_hive_partitioned_false_key_has_no_record_driven_partition_segments(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """With hive_partitioned false, process_record produces a key without partition segments derived from record data (flat or existing behaviour).
    WHAT: Key does not contain year=.../month=.../day=... from record. WHY: Regression guard for non-Hive mode."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": False}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"id": 1, "created_at": "2024-03-11", "region": "eu"}, {})
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    assert "year=2024" not in key or "month=03" not in key or "day=11" not in key, (
        "key must not contain Hive partition segments from record when hive_partitioned is false"
    )


def test_hive_partitioned_true_no_x_partition_fields_key_contains_extraction_date(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """With hive_partitioned true and no x-partition-fields, process_record produces a key containing the extraction date segment.
    WHAT: Key contains year=.../month=.../day=... from extraction_date. WHY: Extraction date path when schema has no partition fields."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"id": 1, "name": "any"}, {})
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    assert "year=2024" in key and "month=03" in key and "day=11" in key, (
        "key must contain extraction date segment when hive_partitioned true and no x-partition-fields"
    )


def test_hive_partitioned_true_x_partition_fields_key_contains_literal_and_date_segments(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """With hive_partitioned true and x-partition-fields [r, d], record with r='x' and d=datetime produces key with literal 'x' and date segment in order.
    WHAT: Key contains literal segment and year=2024/month=03/day=11 in schema order. WHY: Schema-driven partition path in key."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {
        "x-partition-fields": ["r", "d"],
        "properties": {
            "r": {"type": "string"},
            "d": {"type": "string", "format": "date-time"},
        },
        "required": ["r", "d"],
    }
    target = GCSTarget(config=config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema=schema,
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record(
        {"id": 1, "r": "x", "d": datetime(2024, 3, 11)},
        {},
    )
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    literal_segment = "r=x"
    date_segment = "year=2024/month=03/day=11"
    assert literal_segment in key, (
        "key must contain literal partition segment (key=value) from record"
    )
    assert date_segment in key, "key must contain date partition segment"
    idx_literal = key.index(literal_segment)
    idx_date = key.index("year=2024")
    assert idx_literal < idx_date, (
        "literal segment must appear before date segment in key order"
    )


def test_partition_change_closes_handle_two_distinct_keys(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Two records with different partition paths produce two open calls and two distinct keys (handle closed and reopened).
    WHAT: Observable behaviour: two keys, two open calls. WHY: Black-box guard for partition-change handle lifecycle."""
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
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"dt": "2024-03-10", "id": 1}, {})
    sink.process_record({"dt": "2024-03-11", "id": 2}, {})
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2
    keys = [p[1] for p in paths]
    assert keys[0] != keys[1], (
        "two distinct keys must be used when partition path changes"
    )
