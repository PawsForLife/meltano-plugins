"""Tests for GCSSink record serialization: Decimal and non-serializable types."""

from datetime import datetime
from decimal import Decimal

import orjson
import pytest

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_record_with_decimal_serializes_to_valid_json(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Record containing decimal.Decimal is written as valid JSONL with the numeric value as a JSON number.
    Regression guard: orjson does not natively serialize Decimal; the sink will use a default callback (later task).
    WHAT: process_record accepts a record with Decimal and writes JSONL where the value is a number. WHY: prevent regression when adding Decimal support."""
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
    record = {"id": 1, "score": Decimal("12.34")}
    sink.process_record(record, {})
    sink.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) >= 1, "at least one line must be written"
    bucket, key = paths[0]
    content = recording_storage_client.get_written_content(bucket, key)
    assert content is not None
    lines = [line for line in content.split(b"\n") if line.strip()]
    assert len(lines) >= 1
    decoded = orjson.loads(lines[-1].strip())
    assert decoded["score"] == 12.34, (
        "Decimal must appear in written JSON as a numeric value equal to float(Decimal)"
    )


def test_non_serializable_non_decimal_type_raises_type_error(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Record containing a non-JSON-serializable value that is not Decimal raises TypeError when process_record runs.
    Documents the contract that only Decimal is coerced to float; other non-serializable types must raise TypeError
    so unknown types are not silently coerced. Black-box: asserts only that TypeError is raised."""
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
    record = {"id": 1, "bad": object()}
    context = {}
    with pytest.raises(TypeError):
        sink.process_record(record, context)
