"""Path patterns for GCS extraction: Simple, Dated, Partitioned. GCSSink lives in target_gcs.sinks (sinks.py)."""

from target_gcs.constants import (
    FILENAME_TEMPLATE,
    PATH_DATED,
    PATH_PARTITIONED,
    PATH_SIMPLE,
)

from ._types import PathType
from .base import BasePathPattern
from .dated import DatedPath
from .partitioned import PartitionedPath
from .simple import SimplePath

__all__ = [
    "BasePathPattern",
    "DatedPath",
    "FILENAME_TEMPLATE",
    "PartitionedPath",
    "PATH_DATED",
    "PATH_PARTITIONED",
    "PATH_SIMPLE",
    "PathType",
    "SimplePath",
]
