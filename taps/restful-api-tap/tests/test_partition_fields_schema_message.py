"""Integration test: tap emits SCHEMA message with x-partition-fields when partition_fields set.

Verifies the full flow: stream config partition_fields -> schema injection -> SCHEMA message.
"""

import io
import json
from contextlib import redirect_stdout

from restful_api_tap.tap import RestfulApiTap
from tests.test_streams import config, setup_api


def _schema_messages_from_stdout(stdout: str) -> list[dict]:
    """Parse Singer JSON lines from stdout and return SCHEMA-type messages."""
    messages = []
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get("type") == "SCHEMA":
                messages.append(obj)
        except json.JSONDecodeError:
            pass
    return messages


def test_schema_message_includes_x_partition_fields_when_partition_fields_set(
    requests_mock,
):
    """Tap sync emits SCHEMA message with x-partition-fields when stream has partition_fields.

    Black-box: invokes tap.sync_all(), captures stdout, parses SCHEMA messages,
    and asserts schema dict contains x-partition-fields. Validates emitted wire format.
    """
    cfg = config()
    cfg["streams"][0]["partition_fields"] = ["region", "dt"]
    setup_api(requests_mock)

    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    buf = io.StringIO()
    with redirect_stdout(buf):
        tap.sync_all()

    schema_messages = _schema_messages_from_stdout(buf.getvalue())
    assert len(schema_messages) >= 1
    msg = schema_messages[0]
    assert msg["stream"] == "stream_name"
    assert msg["schema"].get("x-partition-fields") == ["region", "dt"]
