"""Tests the Singer target (target-gcs) using the built-in SDK standard target tests.

Uses sample config file contents for target configuration.
"""

from typing import Any, Dict

from singer_sdk.testing import get_target_test_class

from target_gcs.target import GCSTarget

# Minimal config for SDK template tests; matches test_sinks and test_partition_key_generation.
SAMPLE_CONFIG: Dict[str, Any] = {"bucket_name": "test-bucket"}

# Run standard built-in target tests from the SDK (class-based; pytest discovers test methods).
StandardTargetTests = get_target_test_class(
    target_class=GCSTarget,
    config=SAMPLE_CONFIG,
)


class TestGCSTarget(StandardTargetTests):
    """Standard Target Tests for target-gcs."""


# TODO: Create additional tests as appropriate for this target.
