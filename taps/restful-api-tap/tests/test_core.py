"""Tests standard tap features using the built-in SDK tests library.

Uses a config file (dict) and mocked API to run the SDK's tap test class.
"""

from singer_sdk.testing import get_tap_test_class

from restful_api_tap.tap import RestfulApiTap
from tests.test_streams import config, json_resp, url_path


def test_standard_tap_tests(requests_mock):
    """Run standard tap tests from the SDK with config file and mocked stream response."""
    requests_mock.get(url_path(), json=json_resp())
    get_tap_test_class(RestfulApiTap, config=config())
