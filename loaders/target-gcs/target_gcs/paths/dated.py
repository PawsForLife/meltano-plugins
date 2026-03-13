"""Dated path pattern: Hive path from extraction date only."""

from target_gcs.paths.base import BasePathPattern


class DatedPath(BasePathPattern):
    """Hive path from extraction date only; one handle; rotation at limit; -{idx} when chunking."""

    max_size = 1000
