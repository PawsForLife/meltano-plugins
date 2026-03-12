"""Tests for _build_key_for_record and partition/chunking behaviour."""

from collections.abc import Callable
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from dateutil.parser import ParserError

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget

# Fixed fallback date for deterministic partition resolution tests (no datetime.today() in tests).
FALLBACK_DATE = datetime(2024, 3, 11)
DEFAULT_HIVE_FORMAT = "year=%Y/month=%m/day=%d"


def build_sink(
    config=None,
    time_fn=None,
    date_fn: Callable[[], datetime] | None = None,
):
    """Build a sink for the target using the given config (config file contents).
    Optionally pass time_fn for deterministic key generation and date_fn for run-date in tests.
    When partition_date_field is set, schema includes that field (string type) so sink init validation passes."""
    if config is None:
        config = {}
    default_config = {"bucket_name": "test-bucket"}
    config = {**default_config, **config}
    partition_field = config.get("partition_date_field")
    schema = (
        {"properties": {partition_field: {"type": "string"}}, "required": [partition_field]}
        if partition_field
        else {"properties": {}}
    )
    kwargs = {}
    if time_fn is not None:
        kwargs["time_fn"] = time_fn
    if date_fn is not None:
        kwargs["date_fn"] = date_fn
    return GCSSink(
        GCSTarget(config=config),
        "my_stream",
        schema,
        key_properties=config,
        **kwargs,
    )


def _key_from_open_call(call_args: tuple) -> str:
    """Extract GCS object key from smart_open.open first positional arg (gs://bucket/key)."""
    url: str = str(call_args[0][0])
    return url.split("/", 3)[-1]


# --- Key building with partition_date (_build_key_for_record, key_name when partition_date_field set) ---


def test_sink_has_current_partition_path_when_partition_date_field_set():
    """Sink has _current_partition_path when partition_date_field is set. WHAT: Partition state exists when feature enabled.
    WHY: Handle lifecycle (later tasks) relies on this state."""
    subject = build_sink(config={"partition_date_field": "created_at"})
    assert hasattr(subject, "_current_partition_path")
    assert subject._current_partition_path is None


def test_build_key_for_record_differs_by_partition_path():
    """Different partition paths yield different keys. WHAT: _build_key_for_record uses partition_path in the key so records in different partitions get distinct keys. WHY: Core partition-by-field behaviour."""
    fixed_ts = 99999.0
    sink = build_sink(
        config={
            "partition_date_field": "created_at",
            "key_naming_convention": "{stream}/{partition_date}_{timestamp}.jsonl",
        },
        time_fn=lambda: fixed_ts,
        date_fn=lambda: FALLBACK_DATE,
    )
    key_a = sink._build_key_for_record({"id": 1}, "year=2024/month=01/day=01")
    key_b = sink._build_key_for_record({"id": 2}, "year=2024/month=02/day=01")
    assert key_a != key_b
    assert "year=2024/month=01/day=01" in key_a
    assert "year=2024/month=02/day=01" in key_b


def test_build_key_for_record_includes_hive_style_partition_path():
    """Key contains the Hive-style partition path segment. WHAT: Key format is Hive-compatible for BigQuery/Spark discovery. WHY: Downstream consumers expect path like year=YYYY/month=MM/day=DD."""
    fixed_ts = 11111.0
    hive_path = "year=2024/month=03/day=11"
    sink = build_sink(
        config={
            "partition_date_field": "created_at",
            "key_naming_convention": "data/{partition_date}/{stream}_{timestamp}.jsonl",
        },
        time_fn=lambda: fixed_ts,
    )
    key = sink._build_key_for_record({"id": 1}, hive_path)
    assert hive_path in key
    assert "11111" in key


def test_build_key_for_record_uses_fallback_when_partition_path_from_fallback():
    """When partition_path comes from fallback (e.g. missing field), key contains that fallback date segment. WHAT: Missing field does not crash; path uses fallback. WHY: Robustness."""
    fixed_ts = 22222.0
    fallback_path = FALLBACK_DATE.strftime(DEFAULT_HIVE_FORMAT)
    sink = build_sink(
        config={
            "partition_date_field": "created_at",
            "partition_date_format": DEFAULT_HIVE_FORMAT,
            "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
        },
        time_fn=lambda: fixed_ts,
        date_fn=lambda: FALLBACK_DATE,
    )
    key = sink._build_key_for_record({"other": "value"}, fallback_path)
    assert fallback_path in key
    assert "year=2024" in key and "month=03" in key and "day=11" in key


def test_key_name_unchanged_when_partition_date_field_unset():
    """With partition_date_field unset, key_name uses run date and single-key semantics. WHAT: No behaviour change when option unset. WHY: Backward compatibility."""
    date_format = "%Y-%m-%d"
    subject = build_sink({"key_naming_convention": "file/{date}.txt"})
    assert (
        subject.config.get("partition_date_field") is None
        or subject.config.get("partition_date_field") == ""
    )
    assert f"file/{datetime.today().strftime(date_format)}.txt" == subject.key_name


def test_backward_compat_key_name_unchanged_when_partition_date_field_unset():
    """When partition_date_field is unset, key_name uses run date (not record content) and single-key-per-stream semantics are unchanged. WHAT: Explicit backward-compatibility guarantee: no record-driven partition path; key does not depend on record data. WHY: Regression gate and explicit backward-compatibility requirement (task 07)."""
    fixed_date = datetime(2024, 3, 11)
    date_format = "%Y-%m-%d"
    expected_date_str = fixed_date.strftime(date_format)
    subject = build_sink(
        config={"key_naming_convention": "file/{date}.txt"},
        date_fn=lambda: fixed_date,
    )
    assert subject.config.get("partition_date_field") in (None, "")
    assert subject.key_name == f"file/{expected_date_str}.txt"
    with (
        patch("target_gcs.sinks.Client"),
        patch(
            "target_gcs.sinks.smart_open.open", return_value=MagicMock()
        ) as mock_open,
    ):
        context = {}
        for i in range(3):
            subject.process_record(
                {"id": i, "created_at": "2024-01-01", "x": i}, context
            )
        keys_opened = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert mock_open.call_count == 1
    assert keys_opened[0] == f"file/{expected_date_str}.txt"


def test_chunking_with_partition_rotation_within_partition():
    """Chunk rotation within same partition produces two keys with same partition path. WHAT: With partition_date_field and max_records_per_file=2, three records in same partition yield two files (chunk 0 and 1), both under same partition path. WHY: Chunking interaction with partition-by-field."""
    # Same timestamp for first two records (chunk 0), then next for chunk 1 so keys differ only by chunk_index.
    timestamps = iter([3000.0, 3000.0, 3001.0])

    def time_fn():
        return next(timestamps)

    mock_handles = [MagicMock(), MagicMock()]
    with (
        patch("target_gcs.sinks.Client"),
        patch(
            "target_gcs.sinks.smart_open.open", side_effect=mock_handles
        ) as mock_open,
    ):
        sink = build_sink(
            config={
                "partition_date_field": "dt",
                "max_records_per_file": 2,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}_{chunk_index}.jsonl",
            },
            time_fn=time_fn,
            date_fn=lambda: FALLBACK_DATE,
        )
        partition_value = "2024-03-11"
        for i in range(3):
            sink.process_record({"dt": partition_value, "id": i}, {})
    assert mock_open.call_count == 2
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert keys[0] != keys[1]
    partition_segment = "year=2024/month=03/day=11"
    assert partition_segment in keys[0], "first key must contain partition path"
    assert partition_segment in keys[1], "second key must contain same partition path"


def test_partition_change_then_return_creates_three_distinct_keys():
    """Partition A then B then A produces three distinct keys; third key is new file (A'), not reopen of A. WHAT: Option (c) behaviour: on partition return we create a new key, not reopen the old file. WHY: Handle lifecycle and single-handle strategy."""
    timestamps = iter([4000.0, 4001.0, 4002.0])

    def time_fn():
        return next(timestamps)

    with (
        patch("target_gcs.sinks.Client"),
        patch(
            "target_gcs.sinks.smart_open.open",
            side_effect=[MagicMock(), MagicMock(), MagicMock()],
        ) as mock_open,
    ):
        sink = build_sink(
            config={
                "partition_date_field": "dt",
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            time_fn=time_fn,
            date_fn=lambda: FALLBACK_DATE,
        )
        sink.process_record({"dt": "2024-03-10", "id": 1}, {})
        sink.process_record({"dt": "2024-03-11", "id": 2}, {})
        sink.process_record({"dt": "2024-03-10", "id": 3}, {})
    assert mock_open.call_count == 3
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert len(keys) == len(set(keys)), "all three keys must be distinct"
    assert keys[2] != keys[0], "third key (A') must differ from first (A); no reopen"


def test_sink_key_contains_partition_path_from_dateutil_parsable_format():
    """Record with dateutil-parsable non-ISO partition value produces key with expected partition path.
    WHAT: Sink uses helper output for dateutil-only formats; key passed to smart_open.open contains
    the partition path segment (e.g. year=2024/month=03/day=11). WHY: Integration guarantee that
    the full path from record → partition path → key is correct for non-ISO date strings."""
    fixed_ts = 55555.0
    with (
        patch("target_gcs.sinks.Client"),
        patch(
            "target_gcs.sinks.smart_open.open",
            return_value=MagicMock(),
        ) as mock_open,
    ):
        sink = build_sink(
            config={
                "partition_date_field": "created_at",
                "partition_date_format": DEFAULT_HIVE_FORMAT,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            time_fn=lambda: fixed_ts,
            date_fn=lambda: FALLBACK_DATE,
        )
        record = {"id": 1, "created_at": "2024/03/11"}
        sink.process_record(record, {})
    key = _key_from_open_call(mock_open.call_args)
    expected_segment = "year=2024/month=03/day=11"
    assert expected_segment in key, (
        "key must contain partition path from dateutil-parsed value"
    )


def test_sink_raises_parser_error_when_partition_field_unparseable():
    """Unparseable partition field causes ParserError to propagate from the sink.
    WHAT: Record with unparseable partition value (e.g. 'not-a-date') leads to exception;
    observable outcome is exception, not silent write. WHY: Integration guarantee that
    unparseable input fails visibly."""
    with (
        patch("target_gcs.sinks.Client"),
        patch("target_gcs.sinks.smart_open.open", return_value=MagicMock()),
    ):
        sink = build_sink(
            config={
                "partition_date_field": "created_at",
                "partition_date_format": DEFAULT_HIVE_FORMAT,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            time_fn=lambda: 12345.0,
            date_fn=lambda: FALLBACK_DATE,
        )
        record = {"id": 1, "created_at": "not-a-date"}
        with pytest.raises(ParserError):
            sink.process_record(record, {})
