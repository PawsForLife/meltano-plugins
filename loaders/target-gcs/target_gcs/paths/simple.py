"""Simple path pattern: single path per stream, optional chunking by limit."""

from target_gcs.paths.base import BasePathPattern


class SimplePath(BasePathPattern):
    """Single logical path per stream; one handle; rotation at max_records_per_file; -{idx} when chunking."""

    max_size = 1000
