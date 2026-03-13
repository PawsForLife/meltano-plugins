"""Partitioned path pattern: Hive path from schema x-partition-fields."""

from target_gcs.paths.base import BasePathPattern


class PartitionedPath(BasePathPattern):
    """Hive path from schema x-partition-fields; validation at init; handle lifecycle on partition change; -{idx} when chunking."""

    max_size = 1000
