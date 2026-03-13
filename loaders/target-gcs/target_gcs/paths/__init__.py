"""Path patterns for GCS extraction: Simple, Dated, Partitioned. GCSSink lives in target_gcs.sinks (sinks.py)."""

from ._types import PathType
from .base import (
    DEFAULT_KEY_NAMING_CONVENTION,
    DEFAULT_KEY_NAMING_CONVENTION_HIVE,
    BasePathPattern,
)
from .dated import DatedPath
from .partitioned import PartitionedPath
from .simple import SimplePath

__all__ = [
    "BasePathPattern",
    "DatedPath",
    "DEFAULT_KEY_NAMING_CONVENTION",
    "DEFAULT_KEY_NAMING_CONVENTION_HIVE",
    "PartitionedPath",
    "PathType",
    "SimplePath",
]
