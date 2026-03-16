"""Tests the Singer target (target-gcs) using the built-in SDK standard target tests.

Uses the same config as the sample_config fixture (get_target_test_class requires a
config dict at class-definition time, so the value is defined here).
"""

from typing import Any, cast

from singer_sdk.testing import get_target_test_class
from singer_sdk.testing.factory import BaseTestClass

from ..conftest import GCSTargetWithRecordingStorage

# Config for SDK target test class; matches sample_config fixture value.
_TARGET_TEST_CONFIG: dict[str, Any] = {"bucket_name": "test-bucket"}

# Run standard built-in target tests from the SDK (class-based; pytest discovers test methods).
StandardTargetTests = cast(
    type[BaseTestClass],
    get_target_test_class(
        target_class=GCSTargetWithRecordingStorage, config=_TARGET_TEST_CONFIG
    ),
)


# Mypy does not accept variables as base classes; cast above documents the type.
class TestGCSTarget(StandardTargetTests):  # type: ignore[valid-type,misc]
    """Standard Target Tests for target-gcs."""


# TODO: Create additional tests as appropriate for this target.
