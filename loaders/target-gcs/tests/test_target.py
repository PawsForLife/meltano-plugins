"""Tests the Singer target (target-gcs) using the built-in SDK standard target tests.

Uses sample config file contents for target configuration.
"""

from typing import Any, cast
from unittest.mock import MagicMock

from singer_sdk.testing import get_target_test_class
from singer_sdk.testing.factory import BaseTestClass

from target_gcs.target import GCSTarget

# Minimal config for SDK template tests; matches test_sinks and test_partition_key_generation.
SAMPLE_CONFIG: dict[str, Any] = {"bucket_name": "test-bucket"}


class GCSTargetWithMockStorage(GCSTarget):
    """Target subclass that injects a mock GCS client so tests run without ADC."""

    def __init__(self, *, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self._storage_client = MagicMock()


# Run standard built-in target tests from the SDK (class-based; pytest discovers test methods).
StandardTargetTests = cast(
    type[BaseTestClass],
    get_target_test_class(target_class=GCSTargetWithMockStorage, config=SAMPLE_CONFIG),
)


# Mypy does not accept variables as base classes; cast above documents the type.
class TestGCSTarget(StandardTargetTests):  # type: ignore[valid-type,misc]
    """Standard Target Tests for target-gcs."""


# TODO: Create additional tests as appropriate for this target.
