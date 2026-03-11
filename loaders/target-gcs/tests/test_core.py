"""Tests the Singer target (target-gcs) using the built-in SDK standard target tests.

Uses sample config file contents for target configuration.
"""

from typing import Any, Dict

from singer_sdk.testing import get_target_test_class

from gcs_target.target import GCSTarget

# Sample config file contents for the target (minimal).
SAMPLE_CONFIG: Dict[str, Any] = {
    # TODO: Initialize minimal target config file contents
}

# Run standard built-in target tests from the SDK (class-based; pytest discovers test methods).
StandardTargetTests = get_target_test_class(
    target_class=GCSTarget,
    config=SAMPLE_CONFIG,
)


class TestGCSTarget(StandardTargetTests):
    """Standard Target Tests for target-gcs."""


# TODO: Create additional tests as appropriate for this target.
