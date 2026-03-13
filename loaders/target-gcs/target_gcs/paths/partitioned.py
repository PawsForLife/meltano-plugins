"""Partitioned path pattern: Hive path from schema x-partition-fields.

Partition path is resolved per record via get_partition_path_from_schema_and_record;
validation at init via validate_partition_fields_schema; on partition change the
handle is closed and state reset; when a partition returns a new file is created;
rotation at limit within partition; ParserError from unparseable date is propagated.
"""

from __future__ import annotations

from typing import Any

import smart_open

from target_gcs.helpers import (
    get_partition_path_from_schema_and_record,
    validate_partition_fields_schema,
)
from target_gcs.helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT
from target_gcs.paths.base import BasePathPattern

from ._partitioned import get_hive_path_generator

# Fallback when key_naming_convention is not in config (removed in task 03).
_DEFAULT_KEY_TEMPLATE_HIVE = "{stream}/{partition_date}/{timestamp}.{format}"


class PartitionedPath(BasePathPattern):
    """Hive path from schema x-partition-fields; validation at init; handle lifecycle on partition change; -{idx} when chunking.

    Partition path is resolved per record from x-partition-fields via
    get_partition_path_from_schema_and_record. On partition change the handle is
    closed and state reset; when the same partition is seen again a new file is
    created. One handle at a time; rotation at limit within partition.
    """

    def __init__(
        self,
        stream_name: str,
        schema: dict[str, Any],
        config: dict[str, Any],
        partition_fields: list[str],
        *,
        time_fn: Any = None,
        date_fn: Any = None,
        storage_client: Any = None,
        extraction_date: Any = None,
    ) -> None:

        # Validate the Partition Fields
        validate_partition_fields_schema(
            stream_name=stream_name, schema=schema, partition_fields=partition_fields
        )

        self.hive_path_generator = get_hive_path_generator(
            partition_fields=partition_fields, schema=schema
        )

        self.schema = schema
        self.partition_fields = partition_fields
        self._current_partition_path: str | None = None
        super().__init__(
            stream_name=stream_name,
            config=config,
            time_fn=time_fn,
            date_fn=date_fn,
            storage_client=storage_client,
            extraction_date=extraction_date,
        )

    @property
    def key_template(self) -> str:
        return str(
            self.config.get("key_naming_convention", _DEFAULT_KEY_TEMPLATE_HIVE)
        )

    def hive_path(self, record: dict[str, Any]) -> str:
        hive_path_elements = []
        for field_name, generator in self.hive_path_generator:
            val = record.get(field_name)
            hive_path_elements.append(
                generator(field_name, val if val is not None else "")
            )

        return "/".join(hive_path_elements)

    def record_path(self, partition_path: str) -> str:
        """Build object key for the given partition path: stream + partition_date + timestamp + optional chunk_index."""
        fmt = self.get_chunk_format_map()
        fmt["partition_date"] = partition_path
        base = self.key_template.format(**fmt)
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
        key = self.record_path(partition_path)
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
