"""Tests for _build_key_for_record and partition/chunking behaviour."""

from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from dateutil.parser import ParserError as DateutilParserError

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget


@contextmanager
def _patch_all_pattern_modules(open_mock=None, client_mock=None):
    """Patch smart_open.open and Client in all three path modules for GCSSink tests."""
    open_mock = open_mock if open_mock is not None else MagicMock()
    client_mock = client_mock if client_mock is not None else MagicMock()
    with (
        patch("target_gcs.paths.simple.smart_open.open", open_mock),
        patch("target_gcs.paths.simple.Client", client_mock),
        patch("target_gcs.paths.dated.smart_open.open", open_mock),
        patch("target_gcs.paths.dated.Client", client_mock),
        patch("target_gcs.paths.partitioned.smart_open.open", open_mock),
        patch("target_gcs.paths.partitioned.Client", client_mock),
    ):
        yield open_mock, client_mock


# Fixed extraction date for deterministic partition resolution tests (no datetime.today() in tests).
EXTRACTION_DATE = datetime(2024, 3, 11)
DEFAULT_HIVE_FORMAT = "year=%Y/month=%m/day=%d"


def build_sink(
    config=None,
    time_fn=None,
    date_fn: Callable[[], datetime] | None = None,
    schema: dict | None = None,
    stream_name: str = "my_stream",
):
    """Build a sink for the target using the given config (config file contents).
    Optionally pass time_fn, date_fn for deterministic keys; schema and stream_name for hive_partitioned tests.
    When hive_partitioned is true, pass schema with x-partition-fields (and matching properties/required) so init validation passes; if schema omitted and hive_partitioned true, uses default schema with dt."""
    if config is None:
        config = {}
    default_config = {"bucket_name": "test-bucket"}
    config = {**default_config, **config}
    hive = config.get("hive_partitioned", False)
    if hive and schema is None:
        schema = {
            "x-partition-fields": ["dt"],
            "properties": {"dt": {"type": "string"}},
            "required": ["dt"],
        }
    if schema is None:
        schema = {"properties": {}}
    kwargs = {}
    if time_fn is not None:
        kwargs["time_fn"] = time_fn
    if date_fn is not None:
        kwargs["date_fn"] = date_fn
    return GCSSink(
        GCSTarget(config=config),
        stream_name,
        schema,
        key_properties=config,
        **kwargs,
    )


def _key_from_open_call(call_args: tuple) -> str:
    """Extract GCS object key from smart_open.open first positional arg (gs://bucket/key)."""
    url: str = str(call_args[0][0])
    return url.split("/", 3)[-1]


# --- Key building with hive_partitioned (_build_key_for_record, key_name when hive_partitioned set) ---


def test_sink_has_current_partition_path_when_hive_partitioned_set():
    """With hive_partitioned and x-partition-fields, process_record produces a key containing the partition path. WHAT: Partition path appears in key.
    WHY: Black-box guard for partition state; key shape reflects partition. Schema has no format for dt so path is literal dt=value."""
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules():
        subject = build_sink(
            config={"hive_partitioned": True},
            schema=schema,
            date_fn=lambda: EXTRACTION_DATE,
            time_fn=lambda: 99999.0,
        )
        subject.process_record({"id": 1, "dt": "2024-01-01"}, {})
    assert "dt=2024-01-01" in subject.key_name


def test_build_key_for_record_differs_by_partition_path():
    """Different partition paths yield different keys. WHAT: Keys differ when partition path differs. WHY: Core partition-by-field behaviour. Schema has no format so path is literal dt=value."""
    fixed_ts = 99999.0
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules() as (mock_open, _):
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "{stream}/{partition_date}_{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"id": 1, "dt": "2024-01-01"}, {})
        key_a = sink.key_name
        sink.process_record({"id": 2, "dt": "2024-02-01"}, {})
        key_b = sink.key_name
    assert key_a != key_b
    assert "dt=2024-01-01" in key_a
    assert "dt=2024-02-01" in key_b


def test_build_key_for_record_includes_hive_style_partition_path():
    """Key contains the partition path segment. WHAT: Key includes partition path from record. WHY: Path drives object location. Schema has no format so path is literal dt=value."""
    fixed_ts = 11111.0
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules():
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "data/{partition_date}/{stream}_{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"id": 1, "dt": "2024-03-11"}, {})
    key = sink.key_name
    assert "dt=2024-03-11" in key
    assert "11111" in key


def test_build_key_for_record_uses_hive_default_when_hive_partitioned_set_no_key_naming_convention():
    """When hive_partitioned is true and key_naming_convention is omitted, key uses default pattern stream/partition_date/timestamp.jsonl.
    WHAT: Default layout includes partition path. WHY: Regression guard. Schema has no format so partition path is literal dt=value."""
    fixed_ts = 77777.0
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules():
        sink = build_sink(
            config={"hive_partitioned": True},
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"id": 1, "dt": "2024-03-11"}, {})
    key = sink.key_name
    assert "my_stream" in key, "key must contain stream name"
    assert "dt=2024-03-11" in key, "key must contain partition path segment"
    assert "77777" in key, "key must contain deterministic timestamp"
    assert key.endswith(".jsonl"), "key must end with .jsonl"
    flat_default = "my_stream_77777.jsonl"
    assert key != flat_default, "key must not be flat form {stream}_{timestamp}.jsonl"
    assert "/" in key, "key must use layout stream/partition_path/timestamp.jsonl"


def test_build_key_for_record_uses_user_template_when_key_naming_convention_set():
    """When both hive_partitioned and key_naming_convention are set, built key follows the user template.
    WHAT: Sink must use the user's key_naming_convention. WHY: Regression test. Use schema with format so partition_date is Hive date path."""
    fixed_ts = 88888.0
    partition_path = "year=2024/month=03/day=11"
    user_template = "{stream}/dt={partition_date}/{timestamp}.jsonl"
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string", "format": "date-time"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules():
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": user_template,
            },
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"id": 1, "dt": "2024-03-11T00:00:00"}, {})
    key = sink.key_name
    assert "my_stream/" in key, "key must contain stream prefix from user template"
    assert "dt=year=2024" in key, (
        "key must contain user segment dt=... with Hive partition path"
    )
    assert partition_path in key or "year=2024" in key, (
        "key must contain partition path in user format"
    )
    assert "88888" in key, "key must contain deterministic timestamp"
    assert key.endswith(".jsonl"), "key must end with .jsonl"
    assert key == f"my_stream/dt={partition_path}/{fixed_ts:.0f}.jsonl", (
        "key must exactly match user template shape"
    )


def test_build_key_for_record_hive_token_expands_like_partition_date():
    """When key_naming_convention uses {hive}, the key contains the same partition segment as when using {partition_date}.
    WHAT: {hive} is an alias for the partition path. WHY: Regression guard for {hive} alias. Schema has no format so path is literal."""
    fixed_ts = 12345.0
    partition_path = "dt=2024-03-11"  # literal when schema has no format
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules():
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "{stream}/{hive}/{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"id": 1, "dt": "2024-03-11"}, {})
    key = sink.key_name
    assert partition_path in key, (
        "key must contain partition path segment (hive expands like partition_date)"
    )
    assert key == f"my_stream/{partition_path}/{fixed_ts:.0f}.jsonl", (
        "key must match template with {hive} expanded to partition_path"
    )


def test_build_key_for_record_uses_extraction_date_when_partition_path_from_extraction_date():
    """When partition_path comes from extraction date (e.g. missing x-partition-fields), key contains that extraction date segment. WHAT: No partition fields does not crash; path uses extraction date. WHY: Robustness."""
    fixed_ts = 22222.0
    extraction_date_path = EXTRACTION_DATE.strftime(DEFAULT_HIVE_FORMAT)
    schema = {"properties": {}}
    with _patch_all_pattern_modules():
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"other": "value"}, {})
    key = sink.key_name
    assert extraction_date_path in key
    assert "year=2024" in key and "month=03" in key and "day=11" in key


def test_default_key_when_hive_partitioned_and_key_naming_convention_omitted():
    """Default key is {stream}_{timestamp}.jsonl when hive_partitioned is false and key_naming_convention is omitted.
    WHAT: key_name uses non-partition default pattern with no partition path. WHY: Regression gate so conditional-default
    change does not alter behaviour when hive_partitioned is unset."""
    fixed_ts = 12345.0
    with _patch_all_pattern_modules():
        subject = build_sink(config={}, time_fn=lambda: fixed_ts)
        subject.process_record({"id": 1}, {})
    assert subject.config.get("hive_partitioned") is not True
    assert subject.config.get("key_naming_convention") in (None, "")
    expected_key = "my_stream_12345.jsonl"
    assert subject.key_name == expected_key


def test_key_name_unchanged_when_hive_partitioned_unset():
    """With hive_partitioned unset, key_name uses run date and single-key semantics. WHAT: No behaviour change when option unset. WHY: Backward compatibility."""
    date_format = "%Y-%m-%d"
    with _patch_all_pattern_modules():
        subject = build_sink({"key_naming_convention": "file/{date}.txt"})
        subject.process_record({"id": 1}, {})
    assert subject.config.get("hive_partitioned") is not True
    assert f"file/{datetime.today().strftime(date_format)}.txt" == subject.key_name


def test_backward_compat_key_name_unchanged_when_hive_partitioned_unset():
    """When hive_partitioned is unset, key_name uses run date (not record content) and single-key-per-stream semantics are unchanged. WHAT: Explicit backward-compatibility guarantee: no record-driven partition path; key does not depend on record data. WHY: Regression gate and explicit backward-compatibility requirement."""
    fixed_date = datetime(2024, 3, 11)
    date_format = "%Y-%m-%d"
    expected_date_str = fixed_date.strftime(date_format)
    with _patch_all_pattern_modules() as (mock_open, _):
        subject = build_sink(
            config={"key_naming_convention": "file/{date}.txt"},
            date_fn=lambda: fixed_date,
        )
        assert subject.config.get("hive_partitioned") is not True
        context = {}
        for i in range(3):
            subject.process_record(
                {"id": i, "created_at": "2024-01-01", "x": i}, context
            )
        keys_opened = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert subject.key_name == f"file/{expected_date_str}.txt"
    assert mock_open.call_count == 1
    assert keys_opened[0] == f"file/{expected_date_str}.txt"


def test_chunking_with_partition_rotation_within_partition():
    """Chunk rotation within same partition produces two keys with same partition path. WHAT: With hive_partitioned and max_records_per_file=2, three records in same partition yield two files (chunk 0 and 1), both under same partition path. WHY: Chunking interaction with partition-by-field."""
    timestamps = iter([3000.0, 3000.0, 3001.0, 3002.0])

    def time_fn():
        return next(timestamps)

    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    mock_handles = [MagicMock(), MagicMock()]
    with _patch_all_pattern_modules(open_mock=MagicMock(side_effect=mock_handles)) as (
        mock_open,
        _,
    ):
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "max_records_per_file": 2,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}_{chunk_index}.jsonl",
            },
            schema=schema,
            time_fn=time_fn,
            date_fn=lambda: EXTRACTION_DATE,
        )
        partition_value = "2024-03-11"
        for i in range(3):
            sink.process_record({"dt": partition_value, "id": i}, {})
    assert mock_open.call_count == 2
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert keys[0] != keys[1]
    # Schema has no format for dt; string "2024-03-11" is literal segment (key=value form).
    partition_segment = "dt=2024-03-11"
    assert partition_segment in keys[0], "first key must contain partition path"
    assert partition_segment in keys[1], "second key must contain same partition path"


def test_partition_change_then_return_creates_three_distinct_keys():
    """Partition A then B then A produces three distinct keys; third key is new file (A'), not reopen of A. WHAT: On partition return we create a new key, not reopen the old file. WHY: Handle lifecycle and single-handle strategy."""
    timestamps = iter([4000.0, 4001.0, 4002.0])

    def time_fn():
        return next(timestamps)

    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules(
        open_mock=MagicMock(side_effect=[MagicMock(), MagicMock(), MagicMock()])
    ) as (mock_open, _):
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=time_fn,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink.process_record({"dt": "2024-03-10", "id": 1}, {})
        sink.process_record({"dt": "2024-03-11", "id": 2}, {})
        sink.process_record({"dt": "2024-03-10", "id": 3}, {})
    assert mock_open.call_count == 3
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert len(keys) == len(set(keys)), "all three keys must be distinct"
    assert keys[2] != keys[0], "third key (A') must differ from first (A); no reopen"


def test_sink_key_contains_partition_path_from_dateutil_parsable_format():
    """No format → literal segment even for dateutil-parseable string.
    WHAT: Schema has no format for partition field; record value is dateutil-parseable string
    (e.g. '2024/03/11'); key must contain path-safe literal segment (2024_03_11), not Hive date segment.
    WHY: We must not infer date from string content when schema does not declare date/date-time format."""
    fixed_ts = 55555.0
    schema = {
        "x-partition-fields": ["created_at"],
        "properties": {"created_at": {"type": "string"}},
        "required": ["created_at"],
    }
    with _patch_all_pattern_modules() as (mock_open, _):
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=lambda: fixed_ts,
            date_fn=lambda: EXTRACTION_DATE,
        )
        record = {"id": 1, "created_at": "2024/03/11"}
        sink.process_record(record, {})
    key = _key_from_open_call(mock_open.call_args)
    expected_literal_segment = "created_at=2024_03_11"
    assert expected_literal_segment in key, (
        "key must contain path-safe literal segment when schema has no format"
    )
    hive_date_segment = "year=2024/month=03/day=11"
    assert hive_date_segment not in key, (
        "key must not contain Hive date segment when schema has no format (no string date inference)"
    )


def test_sink_uses_literal_segment_when_partition_field_unparseable():
    """Unparseable partition field without date format is treated as a literal path segment (schema-and-record path builder).
    WHAT: Record with unparseable partition value (e.g. 'not-a-date') and no format in schema is written as literal in the key path; no exception. WHY: get_partition_path_from_schema_and_record uses unparseable strings as literal segments when format is not date/date-time."""
    schema = {
        "x-partition-fields": ["created_at"],
        "properties": {"created_at": {"type": "string"}},
        "required": ["created_at"],
    }
    with _patch_all_pattern_modules() as (mock_open, _):
        sink = build_sink(
            config={
                "hive_partitioned": True,
                "key_naming_convention": "{partition_date}/{stream}_{timestamp}.jsonl",
            },
            schema=schema,
            time_fn=lambda: 12345.0,
            date_fn=lambda: EXTRACTION_DATE,
        )
        record = {"id": 1, "created_at": "not-a-date"}
        sink.process_record(record, {})
    key = _key_from_open_call(mock_open.call_args)
    assert "created_at=not-a-date" in key, (
        "unparseable value must appear as key=value literal in key path"
    )


def test_multiple_streams_different_x_partition_fields_order_keys_differ():
    """Two streams with different x-partition-fields order produce keys with segment order matching each stream schema.
    WHAT: Stream A [region, dt] vs stream B [dt, region] yield different key paths for same logical values. WHY: Keys differ per stream; segment order is schema-defined."""
    schema_a = {
        "x-partition-fields": ["region", "dt"],
        "properties": {"region": {"type": "string"}, "dt": {"type": "string"}},
        "required": ["region", "dt"],
    }
    schema_b = {
        "x-partition-fields": ["dt", "region"],
        "properties": {"region": {"type": "string"}, "dt": {"type": "string"}},
        "required": ["dt", "region"],
    }
    record = {"id": 1, "region": "eu", "dt": "2024-03-11"}
    with _patch_all_pattern_modules() as (mock_open_a, _):
        sink_a = build_sink(
            config={"hive_partitioned": True},
            schema=schema_a,
            stream_name="stream_a",
            time_fn=lambda: 50000.0,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink_a.process_record(record, {})
    key_a = _key_from_open_call(mock_open_a.call_args)
    with _patch_all_pattern_modules() as (mock_open_b, _):
        sink_b = build_sink(
            config={"hive_partitioned": True},
            schema=schema_b,
            stream_name="stream_b",
            time_fn=lambda: 50000.0,
            date_fn=lambda: EXTRACTION_DATE,
        )
        sink_b.process_record(record, {})
    key_b = _key_from_open_call(mock_open_b.call_args)
    assert key_a != key_b
    # Schema has no format for dt; keys contain key=value segments (region=eu, dt=2024-03-11).
    segment_region = "region=eu"
    segment_dt = "dt=2024-03-11"
    assert segment_region in key_a and segment_dt in key_a
    assert segment_region in key_b and segment_dt in key_b
    idx_region_a, idx_dt_a = key_a.index(segment_region), key_a.index(segment_dt)
    idx_region_b, idx_dt_b = key_b.index(segment_region), key_b.index(segment_dt)
    assert idx_region_a < idx_dt_a, "stream_a key must have region before date"
    assert idx_dt_b < idx_region_b, "stream_b key must have date before region"


def test_sink_raises_parser_error_when_partition_field_date_format_unparseable():
    """Record with partition field that has format date-time and unparseable string value raises ParserError (path builder propagates).
    WHAT: Schema declares date-time format; value 'not-a-date' cannot be parsed → ParserError. WHY: Fail visibly when date-typed field has invalid value."""
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string", "format": "date-time"}},
        "required": ["dt"],
    }
    with _patch_all_pattern_modules():
        sink = build_sink(
            config={"hive_partitioned": True},
            schema=schema,
            time_fn=lambda: 12345.0,
            date_fn=lambda: EXTRACTION_DATE,
        )
        with pytest.raises(DateutilParserError):
            sink.process_record({"id": 1, "dt": "not-a-date"}, {})
