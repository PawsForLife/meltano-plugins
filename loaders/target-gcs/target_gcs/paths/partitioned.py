"""Partitioned path pattern: Hive path from schema x-partition-fields.

Partition path is resolved per record via get_partition_path_from_schema_and_record;
validation at init via validate_partition_fields_schema; on partition change the
handle is closed and state reset; when a partition returns a new file is created;
rotation at limit within partition; ParserError from unparseable date is propagated.
"""

from __future__ import annotations

from typing import Any

import smart_open
from google.cloud.storage import Client

from target_gcs.helpers import (
    get_partition_path_from_schema_and_record,
    validate_partition_fields_schema,
)
from target_gcs.helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT
from target_gcs.paths.base import BasePathPattern


class PartitionedPath(BasePathPattern):
    """Hive path from schema x-partition-fields; validation at init; handle lifecycle on partition change; -{idx} when chunking.

    Partition path is resolved per record from x-partition-fields via
    get_partition_path_from_schema_and_record. On partition change the handle is
    closed and state reset; when the same partition is seen again a new file is
    created. One handle at a time; rotation at limit within partition.
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
        x_partition_fields = schema.get("x-partition-fields")
        if isinstance(x_partition_fields, list) and len(x_partition_fields) > 0:
            validate_partition_fields_schema(
                stream_name, schema, x_partition_fields
            )
        self._current_partition_path: str | None = None
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

    @property
    def storage_client(self) -> Client:
        """Resolved storage client; creates default Client when not injected."""
        if self._storage_client is None:
            self._storage_client = Client()
        return self._storage_client

    def _build_key(self, partition_path: str) -> str:
        """Build object key for the given partition path: stream + partition_date + timestamp + optional chunk_index."""
        template = self.get_effective_key_template()
        fmt = self.get_chunk_format_map()
        fmt["partition_date"] = partition_path
        fmt["hive"] = partition_path
        base = template.format(**fmt)
        return self.apply_key_prefix_and_normalize(base)

    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Resolve partition path, handle partition change (close + reset), rotate if at limit, open handle if needed, write record. Re-raises ParserError from get_partition_path_from_schema_and_record."""
        partition_path = get_partition_path_from_schema_and_record(
            self.schema,
            record,
            self._extraction_date,
            partition_date_format=DEFAULT_PARTITION_DATE_FORMAT,
        )
        if partition_path != self._current_partition_path:
            self.flush_and_close_handle()
            self._current_partition_path = partition_path
            self._chunk_index = 0
            self._records_written_in_current_file = 0
            self._key_name = ""
        self.maybe_rotate_if_at_limit()
        key = self._build_key(partition_path)
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
