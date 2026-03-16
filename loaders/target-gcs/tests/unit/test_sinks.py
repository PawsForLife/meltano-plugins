"""Tests for the target's sink (GCSSink): key naming, config file schema, and GCS client behaviour."""

import re
from datetime import datetime
from decimal import Decimal

import orjson
import pytest

from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient


def test_public_api_imports_succeed():
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
):
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
):
    """Key format matches {prefix}/{stream}/{path}/{timestamp}.jsonl for each pattern (SimplePath, DatedPath, PartitionedPath).
    WHAT: key_name structure aligns with PATH_SIMPLE, PATH_DATED, PATH_PARTITIONED and FILENAME_TEMPLATE constants.
    WHY: Regression guard that sink delegates to patterns and key shape is fixed by constants (no key_naming_convention)."""

    def time_fn():
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
):
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
):
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
):
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
):
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
    assert subject._extraction_date is not None
    assert subject._extraction_date == fixed_date


def test_config_schema_excludes_key_naming_convention():
    """WHAT: Config schema must not expose key_naming_convention; key shape is fixed by internal constants.
    WHY: Regression guard for config removal (split-path-filename task 03)."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "key_naming_convention" not in properties


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


def test_config_schema_includes_hive_partitioned():
    """Config schema exposes hive_partitioned (boolean, optional) so users can enable Hive-style partitioning from stream schema or current date."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "hive_partitioned" in properties
    prop = properties["hive_partitioned"]
    type_val = prop.get("type")
    assert type_val == "boolean" or (
        isinstance(type_val, list) and "boolean" in type_val
    )
    required = schema.get("required") or []
    assert "hive_partitioned" not in required
    assert prop.get("default") is False


def test_config_schema_omits_partition_date_field():
    """Config schema must not expose partition_date_field; replaced by hive_partitioned in schema-driven Hive partitioning."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "partition_date_field" not in properties


def test_config_schema_omits_partition_date_format():
    """Config schema must not expose partition_date_format; format is internal when using hive_partitioned."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "partition_date_format" not in properties


def test_config_validates_with_hive_partitioned():
    """Config with hive_partitioned true or false is valid; target instantiates and exposes the value (or default false)."""
    config_true = {"bucket_name": "b", "hive_partitioned": True}
    target_true = GCSTarget(config=config_true)
    assert target_true.config["hive_partitioned"] is True
    config_false = {"bucket_name": "b", "hive_partitioned": False}
    target_false = GCSTarget(config=config_false)
    assert target_false.config["hive_partitioned"] is False
    config_omitted = {"bucket_name": "b"}
    target_omitted = GCSTarget(config=config_omitted)
    assert target_omitted.config.get("hive_partitioned") is False


def test_one_key_and_one_handle_when_chunking_disabled(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
):
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
):
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
):
    """Rotation after N records: when max_records_per_file is N, after N records the sink closes the current file and opens a new one; the record that would exceed the limit is written to the new file. Core chunking requirement."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 2}
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0])

    def time_fn():
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
):
    """Every record written exactly once: with chunking enabled, all records are written to GCS with no duplicates or drops. Correctness of the pipeline."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 10}
    timestamps = iter([1000.0 + i for i in range(30)])

    def time_fn():
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


def test_record_with_decimal_serializes_to_valid_json(
    sample_config: dict,
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
):
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
):
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


# --- Hive partition init validation (sink integration) ---


def test_sink_init_hive_partitioned_invalid_x_partition_fields_raises_value_error(
    recording_storage_client: RecordingGCSClient,
):
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
):
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
):
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
):
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
):
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
):
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


# --- Key/path behaviour (black-box: keys via recording client) ---


def test_hive_partitioned_false_key_has_no_record_driven_partition_segments(
    fixed_time_fn: object,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
):
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
):
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
):
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
):
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
