"""Shared pytest fixtures for target-gcs tests.

Canonical approach:
- All tests use RecordingGCSClient for GCS I/O; no real Client and no patching of
  smart_open. Request recording_storage_client fixture when tests need to assert
  on get_written_paths() or get_written_content().
- Tests instantiate classes (GCSTarget, GCSSink, SimplePath, DatedPath, PartitionedPath)
  directly using fixtures (sample_config, fixed_time_fn, fixed_date, recording_storage_client)
  or in-test values when testing a specific config/date/time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest

from target_gcs.target import GCSTarget
from tests.fixtures.recording_gcs_client import RecordingGCSClient

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Return the default target config for tests."""
    return {"bucket_name": "test-bucket"}


@pytest.fixture
def fixed_time_fn() -> Callable[[], float]:
    """Return a callable that yields a fixed timestamp for deterministic keys."""
    return lambda: 12345.0


@pytest.fixture
def fixed_date() -> datetime:
    """Fixed date for assertions and extraction_date in tests."""
    return datetime(2024, 3, 11)


@pytest.fixture
def recording_storage_client() -> RecordingGCSClient:
    """In-memory GCS client for tests; assert via get_written_content and get_written_paths."""
    return RecordingGCSClient()


# -----------------------------------------------------------------------------
# Target with recording storage (for test_target)
# -----------------------------------------------------------------------------


class GCSTargetWithRecordingStorage(GCSTarget):
    """GCSTarget subclass that injects RecordingGCSClient so tests run without ADC.

    test_target imports this from conftest for use with get_target_test_class.
    """

    def __init__(self, *, config: dict[str, Any] | None = None, **kwargs: Any) -> None:
        super().__init__(config=config, storage_client=RecordingGCSClient(), **kwargs)
