"""Tests for the target's sink (GCSSink): key naming, config file schema, and GCS client behaviour."""

import re
from datetime import datetime
from unittest.mock import patch

from gcs_target.sinks import GCSSink
from gcs_target.target import GCSTarget


def build_sink(config=None):
    """Build a sink for the target using the given config (config file contents)."""
    if config is None:
        config = {}
    default_config = {"bucket_name": "test-bucket"}
    config = {**default_config, **config}
    return GCSSink(
        GCSTarget(config=config), "my_stream", {"properties": {}}, key_properties=config
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


def test_config_schema_has_no_credentials_file():
    """Target config file schema must not accept credentials_file; auth uses ADC or GOOGLE_APPLICATION_CREDENTIALS only."""
    schema = GCSTarget.config_jsonschema
    properties = schema.get("properties") or {}
    assert "credentials_file" not in properties


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
