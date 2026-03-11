"""Tests for the target's sink (GCSSink): key naming, config file schema, and GCS client behaviour."""

import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import orjson

from gcs_target.sinks import GCSSink
from gcs_target.target import GCSTarget


def build_sink(config=None, time_fn=None):
    """Build a sink for the target using the given config (config file contents).
    Optionally pass time_fn for deterministic key generation in tests."""
    if config is None:
        config = {}
    default_config = {"bucket_name": "test-bucket"}
    config = {**default_config, **config}
    kwargs = {}
    if time_fn is not None:
        kwargs["time_fn"] = time_fn
    return GCSSink(
        GCSTarget(config=config),
        "my_stream",
        {"properties": {}},
        key_properties=config,
        **kwargs,
    )


def test_extraction_timestamp_is_unix_time():
    subject = build_sink()
    assert re.match(r"my_stream_\d+.jsonl", subject.key_name)


def test_key_name_includes_prefix_when_provided():
    subject = build_sink({"key_prefix": "asdf"})
    assert re.match(r"asdf/my_stream", subject.key_name)


def test_key_name_does_not_start_with_slash():
    subject = build_sink({"key_prefix": "/asdf"})
    assert not subject.key_name.startswith("/")


def test_key_name_includes_stream_name_when_naming_convention_not_provided():
    subject = build_sink({"key_naming_convention": "asdf.txt"})
    assert subject.key_name == "asdf.txt"


def test_key_name_includes_stream_name_if_stream_token_used():
    subject = build_sink({"key_naming_convention": "___{stream}___.txt"})
    assert subject.key_name == "___my_stream___.txt"


def test_key_name_includes_default_date_format_if_date_token_used():
    date_format = "%Y-%m-%d"
    subject = build_sink({"key_naming_convention": "file/{date}.txt"})
    assert f"file/{datetime.today().strftime(date_format)}.txt" == subject.key_name


def test_key_name_includes_date_format_if_date_token_used_and_date_format_provided():
    date_format = "%m %d, %Y"
    subject = build_sink(
        {"key_naming_convention": "file/{date}.txt", "date_format": date_format}
    )
    assert f"file/{datetime.today().strftime(date_format)}.txt" == subject.key_name


def test_key_name_includes_timestamp_if_timestamp_token_used():
    subject = build_sink({"key_naming_convention": "file/{timestamp}.txt"})
    assert re.match(r"file/\d+.txt", subject.key_name)


def test_key_name_uses_injectable_time_fn_when_provided():
    """Key name uses injectable time when time_fn is provided so tests can assert key content without flakiness.
    WHAT: key_name uses time_fn for extraction_timestamp when passed to GCSSink. WHY: deterministic key assertions in tests (e.g. rotation and chunk_index in key)."""
    fixed_ts = 12345.0
    subject = build_sink(
        config={"key_naming_convention": "file/{timestamp}.txt"},
        time_fn=lambda: fixed_ts,
    )
    assert subject.key_name == "file/12345.txt"


def test_config_schema_has_no_credentials_file():
    """Target config file schema must not accept credentials_file; auth uses ADC or GOOGLE_APPLICATION_CREDENTIALS only."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "credentials_file" not in properties


def test_config_schema_includes_max_records_per_file():
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


def test_config_validates_with_max_records_per_file():
    """Config including max_records_per_file is valid; target instantiates without validation error."""
    config = {"bucket_name": "b", "max_records_per_file": 1000}
    target = GCSTarget(config=config)
    assert target.config["max_records_per_file"] == 1000


def test_config_validates_without_max_records_per_file():
    """Config without max_records_per_file is valid; optional property may be omitted."""
    config = {"bucket_name": "b"}
    target = GCSTarget(config=config)
    assert (
        target.config.get("max_records_per_file") is None
        or target.config.get("max_records_per_file") == 0
    )


def test_gcs_client_created_without_credentials_path():
    """Sink must use Client() (ADC) only; no explicit credentials path passed from config file."""
    with patch("gcs_target.sinks.Client") as mock_client:
        sink = build_sink()
        _ = sink.gcs_write_handle
        mock_client.assert_called_once_with()


def test_gcs_client_uses_adc_when_google_application_credentials_set():
    """When GOOGLE_APPLICATION_CREDENTIALS is set, the sink's client is still created with no path (ADC honours env)."""
    with patch("gcs_target.sinks.Client") as mock_client:
        with patch.dict("os.environ", {"GOOGLE_APPLICATION_CREDENTIALS": "/tmp/dummy"}):
            sink = build_sink()
            _ = sink.gcs_write_handle
        mock_client.assert_called_once_with()


def test_one_key_and_one_handle_when_chunking_disabled():
    """When max_records_per_file is unset or 0, multiple records use a single key and a single handle (no rotation).
    Backward compatibility: existing behaviour must be unchanged when the option is off."""
    mock_handle = MagicMock()
    with patch("gcs_target.sinks.Client"), patch(
        "gcs_target.sinks.smart_open.open", return_value=mock_handle
    ) as mock_open:
        sink = build_sink()
        context = {}
        key_after_first = None
        for i in range(5):
            sink.process_record({"id": i, "name": f"record_{i}"}, context)
            if i == 0:
                key_after_first = sink.key_name
        key_after_last = sink.key_name
    assert key_after_first == key_after_last, (
        "key_name must stay stable when chunking is disabled"
    )
    assert mock_open.call_count == 1, (
        "exactly one file handle must be opened for the stream when chunking is off"
    )


def test_key_has_no_chunk_index_when_chunking_disabled():
    """When chunking is disabled, the key must not contain the literal {chunk_index} and must match stream/date/timestamp pattern.
    Backward compatibility: key format is unchanged when chunking is off."""
    with patch("gcs_target.sinks.Client"), patch(
        "gcs_target.sinks.smart_open.open", return_value=MagicMock()
    ):
        sink = build_sink()
        sink.process_record({"id": 1}, {})
    assert "{chunk_index}" not in sink.key_name, (
        "key must not contain chunk_index token when chunking is disabled"
    )
    assert re.match(r"my_stream_\d+\.jsonl", sink.key_name), (
        "key must match default pattern (stream, timestamp) when chunking is off"
    )


def _key_from_open_call(call_args: tuple) -> str:
    """Extract GCS object key from smart_open.open first positional arg (gs://bucket/key)."""
    url = call_args[0][0]
    return url.split("/", 3)[-1]


def test_chunking_rotation_at_threshold():
    """Rotation after N records: when max_records_per_file is N, after N records the sink closes the current file and opens a new one; the record that would exceed the limit is written to the new file. Core chunking requirement."""
    timestamps = iter([1000.0, 1001.0])

    def time_fn():
        return next(timestamps)

    mock_handles = [MagicMock(), MagicMock()]
    with patch("gcs_target.sinks.Client"), patch(
        "gcs_target.sinks.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        sink = build_sink(
            config={
                "max_records_per_file": 2,
                "key_naming_convention": "{stream}_{timestamp}.jsonl",
            },
            time_fn=time_fn,
        )
        context = {}
        for i in range(3):
            sink.process_record({"id": i, "name": f"record_{i}"}, context)
    assert mock_open.call_count == 2, (
        "exactly two file handles must be opened after writing 3 records with max_records_per_file=2"
    )
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert keys[0] != keys[1], "first and second key must differ after rotation"
    third_record_payload = b'{"id":2,"name":"record_2"}\n'
    second_handle_writes = [c[0][0] for c in mock_handles[1].write.call_args_list]
    assert third_record_payload in second_handle_writes, (
        "the third record must be written to the second (new) file"
    )


def test_chunking_key_format_includes_chunk_index():
    """Key includes chunk_index when chunking is on: key_naming_convention may include {chunk_index} so multiple chunks in the same second have distinct keys. Uniqueness when multiple chunks in same second."""
    timestamps = iter([2000.0, 2001.0])

    def time_fn():
        return next(timestamps)

    with patch("gcs_target.sinks.Client"), patch(
        "gcs_target.sinks.smart_open.open", side_effect=[MagicMock(), MagicMock()]
    ) as mock_open:
        sink = build_sink(
            config={
                "max_records_per_file": 2,
                "key_naming_convention": "{stream}_{timestamp}_{chunk_index}.jsonl",
            },
            time_fn=time_fn,
        )
        for i in range(3):
            sink.process_record({"id": i}, {})
    assert mock_open.call_count == 2
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert any("_0." in k or "_0.jsonl" in k for k in keys), (
        "one key must contain chunk index 0 for the first chunk"
    )
    assert any("_1." in k or "_1.jsonl" in k for k in keys), (
        "one key must contain chunk index 1 for the second chunk"
    )


def test_chunking_record_integrity_no_duplicate_or_dropped():
    """Every record written exactly once: with chunking enabled, all records are written to GCS with no duplicates or drops. Correctness of the pipeline."""
    write_payloads = []

    def capture_write(data):
        write_payloads.append(data)

    mock_handles = [MagicMock() for _ in range(4)]
    for h in mock_handles:
        h.write.side_effect = capture_write
    with patch("gcs_target.sinks.Client"), patch(
        "gcs_target.sinks.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        sink = build_sink(config={"max_records_per_file": 10})
        for i in range(25):
            sink.process_record({"id": i, "name": f"row_{i}"}, {})
    assert mock_open.call_count == 3, (
        "25 records with max_records_per_file=10 must produce 3 files (10+10+5)"
    )
    assert len(write_payloads) == 25, "exactly 25 write calls must occur"
    records = [orjson.loads(p.strip()) for p in write_payloads]
    ids = [r["id"] for r in records]
    assert len(ids) == 25 and set(ids) == set(range(25)), (
        "all 25 records must be written exactly once with ids 0..24 (no duplicate or dropped)"
    )
