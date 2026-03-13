"""RecordSink implementation for the GCS target. Each sink handles one stream, receiving SCHEMA, RECORD, and STATE messages from the target and writing record data to the destination (GCS). The sink uses the config file for bucket and key settings. On close or when the target drains the sink (sink drain), buffered data is flushed to the destination."""

from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

from singer_sdk.sinks import RecordSink

from .paths import BasePathPattern, DatedPath, PartitionedPath, SimplePath


class GCSSink(RecordSink):
    """GCS sink implementing RecordSink (one record at a time). Selects one of SimplePath, DatedPath, or PartitionedPath from config and schema and delegates process_record and close to that pattern. Handles one stream; writes records to the destination. Sink drain (flush/close) is performed when the sink is closed."""

    max_size = 1000  # Max records to write in one batch

    def __init__(
        self,
        target,
        stream_name,
        schema,
        key_properties,
        *,
        time_fn: Callable[[], float] | None = None,
        date_fn: Callable[[], datetime] | None = None,
        storage_client: Any | None = None,
    ):
        super().__init__(
            target=target,
            stream_name=stream_name,
            schema=schema,
            key_properties=key_properties,
        )
        self._target_ref = target  # Keep reference for pattern constructors (SDK may not expose .target).
        self._time_fn: Callable[[], float] | None = time_fn
        self._date_fn: Callable[[], datetime] | None = date_fn
        self._extraction_date = self._date_fn() if self._date_fn else datetime.today()
        self._storage_client: Any | None = storage_client

        # Select extraction pattern: hive_partitioned false/unset → SimplePath;
        # hive_partitioned true + non-empty x-partition-fields → PartitionedPath;
        # hive_partitioned true + no/empty x-partition-fields → DatedPath.
        hive = self.config.get("hive_partitioned")
        x_partition_fields = self.schema.get("x-partition-fields")
        has_partition_fields = (
            isinstance(x_partition_fields, list) and len(x_partition_fields) > 0
        )
        schema = dict(self.schema)
        key_props = list(self.key_properties) if self.key_properties else []
        config = dict(self.config)
        if not hive:
            self._extraction_pattern: BasePathPattern = cast(
                BasePathPattern,
                SimplePath(
                    self._target_ref,
                    self.stream_name,
                    schema,
                    key_props,
                    config,
                    time_fn=self._time_fn,
                    date_fn=self._date_fn,
                    storage_client=self._storage_client,
                    extraction_date=self._extraction_date,
                ),
            )
        elif has_partition_fields:
            self._extraction_pattern = cast(
                BasePathPattern,
                PartitionedPath(
                    self._target_ref,
                    self.stream_name,
                    schema,
                    key_props,
                    config,
                    time_fn=self._time_fn,
                    date_fn=self._date_fn,
                    storage_client=self._storage_client,
                    extraction_date=self._extraction_date,
                ),
            )
        else:
            self._extraction_pattern = cast(
                BasePathPattern,
                DatedPath(
                    self._target_ref,
                    self.stream_name,
                    schema,
                    key_props,
                    config,
                    time_fn=self._time_fn,
                    date_fn=self._date_fn,
                    storage_client=self._storage_client,
                    extraction_date=self._extraction_date,
                ),
            )

    def process_record(self, record: dict, context: dict) -> None:
        """Process one record (RECORD message payload). Delegates to the selected extraction pattern."""
        self._extraction_pattern.process_record(record, context)

    def close(self) -> None:
        """Flush and close the pattern's write handle. Called on sink drain/teardown."""
        self._extraction_pattern.close()

    @property
    def key_name(self) -> str:
        """Current object key after a write; delegates to the pattern's current_key."""
        return self._extraction_pattern.current_key

    @property
    def storage_client(self):
        """Storage client used for GCS writes; returns injectable or pattern's client."""
        return self._extraction_pattern.storage_client

    @property
    def output_format(self) -> str:
        """Output file format; currently only jsonl is supported."""
        return "jsonl"
