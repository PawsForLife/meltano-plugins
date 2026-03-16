"""Simple path pattern: single path per stream, optional chunking by limit."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import smart_open

from target_gcs.constants import PATH_SIMPLE
from target_gcs.paths.base import BasePathPattern


class SimplePath(BasePathPattern):
    """SimplePath pattern: one path per stream, one file handle, with optional rotation at max_records_per_file.

    This pattern does not use hive partitioning. All records for a stream are written to the same path
    (optionally chunked by file size/record limit).

    Args:
        stream_name (str): Name of the stream (used as path key prefix).
        config (dict[str, Any]): Target or path configuration, containing at least "bucket_name".
        time_fn (Callable[[], float], optional): Function returning the current timestamp as float. Defaults to None.
        storage_client (Any): Required GCS client or test double for writing files; cannot be None.
        extraction_date (datetime): Extraction date for path formatting; must be a datetime, cannot be None.

    Attributes:
        _path (str): The computed path for the stream and extraction date (format: "{stream}/{date}").
    """

    def __init__(
        self,
        *,
        stream_name: str,
        config: dict[str, Any],
        extraction_date: datetime,
        time_fn: Callable[[], float] | None = None,
        storage_client: Any,
    ) -> None:
        super().__init__(
            stream_name=stream_name,
            config=config,
            time_fn=time_fn,
            storage_client=storage_client,
            extraction_date=extraction_date,
        )
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
