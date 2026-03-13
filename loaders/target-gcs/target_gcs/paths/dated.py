"""Dated path pattern: hive-by-extraction-date; fixed partition for run, one handle, rotate at limit."""

from __future__ import annotations

from typing import Any

import smart_open

from target_gcs.constants import DEFAULT_PARTITION_DATE_FORMAT, PATH_DATED
from target_gcs.paths.base import BasePathPattern


class DatedPath(BasePathPattern):
    """Hive path from extraction date only; one handle per run; rotation at limit (timestamp-only).

    Partition path is fixed for the run (extraction_date via DEFAULT_PARTITION_DATE_FORMAT).
    Key = stream + partition_path + timestamp. Same rotate/write/close semantics as SimplePath.
    """

    def __init__(
        self,
        stream_name: str,
        config: dict[str, Any],
        *,
        time_fn: Any = None,
        date_fn: Any = None,
        storage_client: Any = None,
        extraction_date: Any = None,
    ) -> None:
        super().__init__(
            stream_name=stream_name,
            config=config,
            time_fn=time_fn,
            date_fn=date_fn,
            storage_client=storage_client,
            extraction_date=extraction_date,
        )
        hive_path: str = self._extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)
        self._path: str = PATH_DATED.format(stream=stream_name, hive_path=hive_path)

    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Rotate if at limit, ensure handle open, write record as JSONL, set current key."""
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
