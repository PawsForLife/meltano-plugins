"""Simple path pattern: single path per stream, optional chunking by limit."""

from __future__ import annotations

from typing import Any

import smart_open

from target_gcs.constants import PATH_SIMPLE
from target_gcs.paths.base import BasePathPattern


class SimplePath(BasePathPattern):
    """Non-hive-partitioned pattern: one path per stream, one handle, rotation at max_records_per_file (timestamp-only)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        date_fmt = self.config.get("date_format", "%Y-%m-%d")
        date_str = self._extraction_date.strftime(date_fmt)
        self._path = PATH_SIMPLE.format(stream=self.stream_name, date=date_str)

    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Rotate if at limit, ensure handle open, write record as JSONL, and set current key."""
        self.maybe_rotate_if_at_limit()
        filename = self.filename_for_current_file()
        key = self.full_key(self._path, filename)
        self._key_name = key
        if self._current_handle is None:
            uri = f"gs://{self.bucket_name}/{key}"
            self._current_handle = smart_open.open(
                uri,
                "wb",
                transport_params={"client": self.storage_client},
            )
        self.write_record_as_jsonl(record)

    def close(self) -> None:
        """Flush and close the current write handle."""
        self.flush_and_close_handle()
