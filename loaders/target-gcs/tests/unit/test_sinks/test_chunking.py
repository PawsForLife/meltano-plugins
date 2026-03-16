"""Tests for GCSSink record chunking: rotation at threshold and record integrity."""

import re
from datetime import datetime

import orjson

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_one_key_and_one_handle_when_chunking_disabled(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """When max_records_per_file is unset or 0, multiple records use a single key and a single handle (no rotation).
    Backward compatibility: existing behaviour must be unchanged when the option is off."""
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    context = {}
    key_after_first = None
    for i in range(5):
        sink.process_record({"id": i, "name": f"record_{i}"}, context)
        if i == 0:
            key_after_first = sink.key_name
        key_after_last = sink.key_name
    sink.close()
    assert key_after_first == key_after_last, (
        "key_name must stay stable when chunking is disabled"
    )
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1, (
        "exactly one file handle must be opened for the stream when chunking is off"
    )


def test_key_has_no_chunk_index_when_chunking_disabled(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """When chunking is disabled, the key must not contain the literal {chunk_index} and must match stream/date/timestamp.jsonl pattern.
    Key format uses path + filename (split-path-filename)."""
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    sink = GCSSink(
        target=target,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )
    sink.process_record({"id": 1}, {})
    assert "{chunk_index}" not in sink.key_name, (
        "key must not contain chunk_index token when chunking is disabled"
    )
    assert re.match(r"my_stream/\d{4}-\d{2}-\d{2}/\d+\.jsonl", sink.key_name), (
        "key must match default pattern (stream/date/timestamp) when chunking is off"
    )


def test_chunking_rotation_at_threshold(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Rotation after N records: when max_records_per_file is N, after N records the sink closes the current file and opens a new one; the record that would exceed the limit is written to the new file. Core chunking requirement."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 2}
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0])

    def time_fn() -> float:
        return next(timestamps)

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
    context = {}
    for i in range(3):
        sink.process_record({"id": i, "name": f"record_{i}"}, context)
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2, (
        "exactly two file handles must be opened after writing 3 records with max_records_per_file=2"
    )
    keys = [p[1] for p in paths]
    assert keys[0] != keys[1], "first and second key must differ after rotation"
    bucket0, key0 = paths[0]
    bucket1, key1 = paths[1]
    content1 = recording_storage_client.get_written_content(bucket1, key1)
    assert content1 is not None
    assert b'"id":2,"name":"record_2"' in content1, (
        "the third record must be written to the second (new) file"
    )


def test_chunking_record_integrity_no_duplicate_or_dropped(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Every record written exactly once: with chunking enabled, all records are written to GCS with no duplicates or drops. Correctness of the pipeline."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 10}
    timestamps = iter([1000.0 + i for i in range(30)])

    def time_fn() -> float:
        return next(timestamps)

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
    for i in range(25):
        sink.process_record({"id": i, "name": f"row_{i}"}, {})
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 3, (
        "25 records with max_records_per_file=10 must produce 3 files (10+10+5)"
    )
    write_payloads: list[bytes] = []
    for bucket, key in paths:
        content = recording_storage_client.get_written_content(bucket, key)
        assert content is not None
        write_payloads.extend(content.split(b"\n"))
    write_payloads = [p for p in write_payloads if p.strip()]
    assert len(write_payloads) == 25, "exactly 25 write calls must occur"
    records = [orjson.loads(p.strip()) for p in write_payloads]
    ids = [r["id"] for r in records]
    assert len(ids) == 25 and set(ids) == set(range(25)), (
        "all 25 records must be written exactly once with ids 0..24 (no duplicate or dropped)"
    )
