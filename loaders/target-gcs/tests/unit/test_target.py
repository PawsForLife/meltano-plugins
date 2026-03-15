"""Tests the Singer target (target-gcs) using the built-in SDK standard target tests.

Uses sample config file contents for target configuration.
"""

from typing import cast

from singer_sdk.testing import get_target_test_class
from singer_sdk.testing.factory import BaseTestClass

from ..conftest import GCSTargetWithMockStorage, SAMPLE_CONFIG

# Run standard built-in target tests from the SDK (class-based; pytest discovers test methods).
StandardTargetTests = cast(
    type[BaseTestClass],
    get_target_test_class(target_class=GCSTargetWithMockStorage, config=SAMPLE_CONFIG),
)


# Mypy does not accept variables as base classes; cast above documents the type.
class TestGCSTarget(StandardTargetTests):  # type: ignore[valid-type,misc]
    """Standard Target Tests for target-gcs."""


# TODO: Create additional tests as appropriate for this target.
