"""Shared pytest fixtures and factory helpers for target-gcs tests.

Canonical approach:
- Use the mock_storage_client fixture or pass it into build_sink / path builders when
  building targets or paths that need a mock GCS client.
- Use the patch_all_pattern_modules fixture for sink tests that need a patched
  environment (smart_open.open and Client); path tests may use per-pattern patches or
  this fixture.
- Do not add new ad hoc mock client or patch patterns in test files; use these
  fixtures and factories so behaviour stays consistent and maintainable.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from target_gcs.paths import DatedPath, PartitionedPath, SimplePath
from target_gcs.sinks import GCSSink
from target_gcs.target import GCSTarget

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

SAMPLE_CONFIG: dict[str, Any] = {"bucket_name": "test-bucket"}
FIXED_DATE: datetime = datetime(2024, 3, 11)
DEFAULT_STREAM_NAME: str = "my_stream"

# Fixed timestamp for deterministic key filenames in tests.
FIXED_TIMESTAMP: float = 12345.0

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Return a copy of the default target config (SAMPLE_CONFIG)."""
    return deepcopy(SAMPLE_CONFIG)


@pytest.fixture
def fixed_time_fn() -> Callable[[], float]:
    """Return a callable that yields a fixed timestamp for deterministic keys."""
    return lambda: FIXED_TIMESTAMP


@pytest.fixture
def fixed_date_fn() -> Callable[[], datetime]:
    """Return a callable that yields FIXED_DATE for deterministic partition paths."""
    return lambda: FIXED_DATE


@pytest.fixture
def fixed_date() -> datetime:
    """The fixed date value (FIXED_DATE) for assertions."""
    return FIXED_DATE


@pytest.fixture
def mock_storage_client() -> MagicMock:
    """Mock GCS Client for tests that inject storage_client into target/sink/paths."""
    return MagicMock()


@pytest.fixture
def mock_open_handle() -> MagicMock:
    """Mock return value of smart_open.open for tests that assert on writes or key args."""
    return MagicMock()


@pytest.fixture
def patch_all_pattern_modules(
    mock_open_handle: MagicMock,
    mock_storage_client: MagicMock,
):
    """Patch smart_open.open (simple, dated, partitioned) and Client; yield (open_mock, client_mock).

    Use this fixture in sink tests so GCSSink and path code use mocks regardless of
    which pattern is selected. Patches are applied for the duration of the test.
    """
    open_mock = mock_open_handle
    client_mock = mock_storage_client
    with (
        patch("target_gcs.paths.simple.smart_open.open", open_mock),
        patch("target_gcs.paths.dated.smart_open.open", open_mock),
        patch("target_gcs.paths.partitioned.smart_open.open", open_mock),
        patch("target_gcs.paths.base.Client", client_mock),
    ):
        yield open_mock, client_mock


# -----------------------------------------------------------------------------
# Factory functions (plain functions, not fixtures)
# -----------------------------------------------------------------------------


def build_sink(
    config: dict[str, Any] | None = None,
    time_fn: Callable[[], float] | None = None,
    date_fn: Callable[[], datetime] | None = None,
    storage_client: Any | None = None,
    schema: dict[str, Any] | None = None,
    stream_name: str | None = None,
    **kwargs: Any,
) -> GCSSink:
    """Build a GCSSink with merged config and optional injectables.

    Merges config with SAMPLE_CONFIG, builds GCSTarget(config) and
    GCSSink(target, stream_name, schema, key_properties, ...). Passes through
    time_fn, date_fn, storage_client and extra kwargs to GCSSink.
    """
    merged = {**SAMPLE_CONFIG, **(config or {})}
    target = GCSTarget(config=merged)
    name = stream_name if stream_name is not None else DEFAULT_STREAM_NAME
    sink_schema = schema if schema is not None else {"properties": {}}
    key_properties = merged.get("key_properties", merged)
    sink_kwargs: dict[str, Any] = {}
    if time_fn is not None:
        sink_kwargs["time_fn"] = time_fn
    if date_fn is not None:
        sink_kwargs["date_fn"] = date_fn
    if storage_client is not None:
        sink_kwargs["storage_client"] = storage_client
    sink_kwargs.update(kwargs)
    return GCSSink(
        target=target,
        stream_name=name,
        schema=sink_schema,
        key_properties=key_properties,
        **sink_kwargs,
    )


def build_simple_path(
    config: dict[str, Any] | None = None,
    time_fn: Callable[[], float] | None = None,
    date_fn: Callable[[], datetime] | None = None,
    storage_client: Any | None = None,
    extraction_date: datetime | None = None,
    *,
    stream_name: str | None = None,
) -> SimplePath:
    """Build SimplePath with merged config and optional injectables."""
    merged = {**SAMPLE_CONFIG, **(config or {})}
    stream = stream_name if stream_name is not None else DEFAULT_STREAM_NAME
    return SimplePath(
        stream_name=stream,
        config=merged,
        time_fn=time_fn,
        date_fn=date_fn,
        storage_client=storage_client,
        extraction_date=extraction_date,
    )


def build_dated_path(
    config: dict[str, Any] | None = None,
    time_fn: Callable[[], float] | None = None,
    date_fn: Callable[[], datetime] | None = None,
    storage_client: Any | None = None,
    extraction_date: datetime | None = None,
    *,
    stream_name: str | None = None,
) -> DatedPath:
    """Build DatedPath with merged config (hive_partitioned=True) and optional injectables."""
    merged = {
        **SAMPLE_CONFIG,
        "hive_partitioned": True,
        **(config or {}),
    }
    stream = stream_name if stream_name is not None else DEFAULT_STREAM_NAME
    return DatedPath(
        stream_name=stream,
        config=merged,
        time_fn=time_fn,
        date_fn=date_fn,
        storage_client=storage_client,
        extraction_date=extraction_date,
    )


def build_partitioned_path(
    schema: dict[str, Any],
    partition_fields: list[str],
    config: dict[str, Any] | None = None,
    time_fn: Callable[[], float] | None = None,
    date_fn: Callable[[], datetime] | None = None,
    storage_client: Any | None = None,
    *,
    stream_name: str | None = None,
    extraction_date: datetime | None = None,
) -> PartitionedPath:
    """Build PartitionedPath with merged config and optional injectables."""
    merged = {
        **SAMPLE_CONFIG,
        "hive_partitioned": True,
        **(config or {}),
    }
    stream = stream_name if stream_name is not None else DEFAULT_STREAM_NAME
    return PartitionedPath(
        stream_name=stream,
        schema=schema,
        config=merged,
        partition_fields=partition_fields,
        time_fn=time_fn,
        date_fn=date_fn,
        storage_client=storage_client,
        extraction_date=extraction_date,
    )


# -----------------------------------------------------------------------------
# Target with mock storage (for test_target)
# -----------------------------------------------------------------------------


class GCSTargetWithMockStorage(GCSTarget):
    """GCSTarget subclass that injects a mock GCS client so tests run without ADC.

    test_target imports this from conftest for use with get_target_test_class.
    """

    def __init__(self, *, config: dict[str, Any] | None = None, **kwargs: Any) -> None:
        super().__init__(config=config, **kwargs)
        self._storage_client = MagicMock()
