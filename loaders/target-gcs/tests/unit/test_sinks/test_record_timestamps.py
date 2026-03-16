"""Tests for GCSSink record timestamp parsing: non-ISO date strings via dateutil.

WHAT: Record date-time fields in formats like 'YYYY-MM-DD HH:MM:SS UTC' are parsed
successfully; unparseable values are handled per datetime_error_treatment.
WHY: Prevent regression when using dateutil for record-level timestamp parsing
(fix for ValueError on non-ISO strings from taps).
"""

from __future__ import annotations

from datetime import datetime

import pytest

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def _sink_with_datetime_schema(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> GCSSink:
    """Build a GCSSink with a schema that has a date-time property."""
    target = GCSTarget(config=sample_config, storage_client=recording_storage_client)
    return GCSSink(
        target=target,
        stream_name="test_stream",
        schema={
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
            },
        },
        key_properties=[],
        storage_client=recording_storage_client,
        time_fn=fixed_time_fn,
        extraction_date=fixed_date,
    )


def test_record_with_non_iso_datetime_string_parsed_successfully(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Record with non-ISO datetime string (e.g. '2024-05-13 02:17:54 UTC') is parsed without error.

    WHAT: _validate_and_parse accepts a record whose date-time field is a non-ISO string.
    WHY: Taps may emit 'YYYY-MM-DD HH:MM:SS UTC'; target must parse via dateutil."""
    sink = _sink_with_datetime_schema(
        sample_config, fixed_time_fn, fixed_date, recording_storage_client
    )
    record = {"created_at": "2024-05-13 02:17:54 UTC"}
    result = sink._validate_and_parse(record)
    assert result["created_at"] is not None
    assert isinstance(result["created_at"], datetime), (
        "created_at must be parsed to datetime"
    )
    assert result["created_at"].year == 2024
    assert result["created_at"].month == 5
    assert result["created_at"].day == 13


def test_record_with_unparseable_datetime_string_raises(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """Record with unparseable date-time string raises (default treatment is ERROR).

    WHAT: _validate_and_parse with invalid date string leads to ValueError or ParserError.
    WHY: Unparseable values must not be silently ignored; treatment drives behaviour."""
    sink = _sink_with_datetime_schema(
        sample_config, fixed_time_fn, fixed_date, recording_storage_client
    )
    record = {"created_at": "not-a-date"}
    with pytest.raises((ValueError, Exception)) as exc_info:
        sink._validate_and_parse(record)
    assert "created_at" in str(exc_info.value).lower() or "parse" in str(
        exc_info.value
    ).lower()
