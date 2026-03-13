"""Dated path pattern: hive-by-extraction-date; fixed partition for run, one handle, rotate at limit."""

from __future__ import annotations

from typing import Any

import smart_open

from target_gcs.helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT
from target_gcs.paths.base import BasePathPattern

# Fallback when key_naming_convention is not in config (removed in task 03).
_DEFAULT_KEY_TEMPLATE_HIVE = "{stream}/{partition_date}/{timestamp}.{format}"


class DatedPath(BasePathPattern):
    """Hive path from extraction date only; one handle per run; rotation at limit; -{idx} when chunking.

    Partition path is fixed for the run (extraction_date via DEFAULT_PARTITION_DATE_FORMAT).
    Key = stream + partition_path + timestamp + optional chunk_index. Same rotate/write/close
    semantics as SimplePath.
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
        self._partition_path: str = self._extraction_date.strftime(
            DEFAULT_PARTITION_DATE_FORMAT
        )

    @property
    def key_template(self) -> str:
        return str(
            self.config.get("key_naming_convention", _DEFAULT_KEY_TEMPLATE_HIVE)
        )

    def _build_key(self) -> str:
        """Build current object key: stream + partition_date + timestamp + optional chunk_index."""
        fmt = self.get_chunk_format_map()
        fmt["partition_date"] = self._partition_path
        base = self.key_template.format(**fmt)
        return self.apply_key_prefix_and_normalize(base)

    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Rotate if at limit, ensure handle open, write record as JSONL, set current key."""
        self.maybe_rotate_if_at_limit()
        key = self._build_key()
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
