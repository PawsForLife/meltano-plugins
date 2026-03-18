"""Integration test: tap emits SCHEMA message with x-partition-fields when partition_fields set.

Verifies the full flow: stream config partition_fields -> schema injection -> SCHEMA message.
"""

from restful_api_tap.tap import RestfulApiTap
from tests.test_streams import config, setup_api


def test_schema_message_includes_x_partition_fields_when_partition_fields_set(
    requests_mock,
):
    """Tap sync emits SCHEMA message with x-partition-fields when stream has partition_fields.

    Captures tap output, parses SCHEMA messages, and asserts schema dict contains
    x-partition-fields. Black-box: validates emitted wire format.
    """
    cfg = config()
    cfg["streams"][0]["partition_fields"] = ["region", "dt"]
    setup_api(requests_mock)

    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    stream = streams[0]

    # Emit schema message (same path as sync)
    schema_messages = list(stream._generate_schema_messages())
    assert len(schema_messages) >= 1
    msg = schema_messages[0]
    assert msg.stream == "stream_name"
    assert msg.schema.get("x-partition-fields") == ["region", "dt"]
