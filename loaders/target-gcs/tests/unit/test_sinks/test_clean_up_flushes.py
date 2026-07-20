"""End-of-pipe clean_up must commit GCS objects without an explicit close() call."""

from __future__ import annotations

import json

from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_process_endofpipe_commits_records_without_explicit_close(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: SCHEMA + RECORD then process_endofpipe writes a GCS object.

    WHY: Singer SDK calls sink.clean_up() at end-of-pipe, not sink.close().
    If clean_up does not flush/close the smart_open handle, Meltano reports
    record_count > 0 while the bucket only gets Meltano state files.
    """
    target = GCSTarget(
        config={
            "bucket_name": "test-bucket",
            "hive_partitioned": True,
            "key_prefix": "extracts",
        },
        storage_client=recording_storage_client,
    )
    lines = [
        json.dumps(
            {
                "type": "SCHEMA",
                "stream": "campaigns",
                "schema": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}},
                },
                "key_properties": ["id"],
            }
        ),
        json.dumps(
            {
                "type": "RECORD",
                "stream": "campaigns",
                "record": {"id": 1},
            }
        ),
    ]
    target.process_lines(lines)
    assert recording_storage_client.get_written_paths() == []

    target.process_endofpipe()

    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    bucket, key = paths[0]
    assert bucket == "test-bucket"
    assert key.startswith("extracts/campaigns/")
    assert key.endswith(".jsonl")
    content = recording_storage_client.get_written_content(bucket, key)
    assert content is not None
    assert b'"id":1' in content
