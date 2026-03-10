"""Tests the Singer target (target-gcs) using the built-in SDK standard target tests.

Uses sample config file contents for target configuration.
"""

from typing import Any, Dict

from singer_sdk.testing import get_standard_target_tests

from gcs_target.target import GCSTarget

# Sample config file contents for the target (minimal).
SAMPLE_CONFIG: Dict[str, Any] = {
    # TODO: Initialize minimal target config file contents
}


# Run standard built-in target tests from the SDK:
def test_standard_target_tests():
    """Run standard target tests from the SDK for this target using sample config."""
    tests = get_standard_target_tests(
        GCSTarget,
        config=SAMPLE_CONFIG,
    )
    for test in tests:
        test()


# TODO: Create additional tests as appropriate for this target.
