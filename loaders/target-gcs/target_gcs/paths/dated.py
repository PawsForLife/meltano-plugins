"""Dated path pattern: hive-by-extraction-date; fixed partition for run, one handle, rotate at limit."""

from __future__ import annotations

from typing import Any

import smart_open
from google.cloud.storage import Client

from target_gcs.helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT
from target_gcs.paths.base import BasePathPattern


class DatedPath(BasePathPattern):
    """Hive path from extraction date only; one handle per run; rotation at limit; -{idx} when chunking.

    Partition path is fixed for the run (extraction_date via DEFAULT_PARTITION_DATE_FORMAT).
    Key = stream + partition_path + timestamp + optional chunk_index. Same rotate/write/close
    semantics as SimplePath.
    """

    max_size = 1000

    def __init__(
        self,
        target: Any,
        stream_name: str,
        schema: dict[str, Any],
        key_properties: list[str],
        config: dict[str, Any],
        *,
        time_fn: Any = None,
        date_fn: Any = None,
        storage_client: Any = None,
        extraction_date: Any = None,
    ) -> None:
        super().__init__(
            target=target,
            stream_name=stream_name,
            schema=schema,
            key_properties=key_properties,
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
    def storage_client(self) -> Client:
        """Resolved storage client; creates default Client when not injected."""
        if self._storage_client is None:
            self._storage_client = Client()
        return self._storage_client

    def _build_key(self) -> str:
        """Build current object key: stream + partition_date + timestamp + optional chunk_index."""
        template = self.get_effective_key_template()
        fmt = self.get_chunk_format_map()
        fmt["partition_date"] = self._partition_path
        base = template.format(**fmt)
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
