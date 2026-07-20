"""RecordSink implementation for the GCS target. Each sink handles one stream, receiving SCHEMA, RECORD, and STATE messages from the target and writing record data to the destination (GCS). The sink uses the config file for bucket and key settings. On close or when the target drains the sink (sink drain), buffered data is flushed to the destination."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError as DateutilParserError
from singer_sdk.helpers._compat import time_fromisoformat
from singer_sdk.helpers._typing import (
    DatetimeErrorTreatmentEnum,
    get_datelike_property_type,
    handle_invalid_timestamp_in_record,
)
from singer_sdk.sinks import RecordSink

from .paths import BasePathPattern, DatedPath, PartitionedPath, SimplePath


class GCSSink(RecordSink):
    """GCS sink implementing RecordSink (one record at a time). Selects one of SimplePath, DatedPath, or PartitionedPath from config and schema and delegates process_record and close to that pattern. Handles one stream; writes records to the destination. Sink drain (flush/close) is performed when the sink is closed. Provides extraction_date from datetime.today() when not injected (e.g. for tests)."""

    max_size = 1000  # Max records to write in one batch

    def __init__(
        self,
        target,
        stream_name,
        schema,
        key_properties,
        storage_client: Any,
        time_fn: Callable[[], float] | None = None,
        extraction_date: datetime | None = None,
    ):
        super().__init__(
            target=target,
            stream_name=stream_name,
            schema=schema,
            key_properties=key_properties,
        )
        self._target_ref = target  # Keep reference for pattern constructors (SDK may not expose .target).
        self._time_fn: Callable[[], float] | None = time_fn
        self._storage_client: Any = storage_client
        self._extraction_date: datetime = (
            extraction_date if extraction_date is not None else datetime.today()
        )

        # Select extraction pattern: hive_partitioned false/unset → SimplePath;
        # hive_partitioned true + non-empty x-partition-fields → PartitionedPath;
        # hive_partitioned true + no/empty x-partition-fields → DatedPath.
        hive = self.config.get("hive_partitioned")
        x_partition_fields = self.schema.get("x-partition-fields")
        has_partition_fields = (
            isinstance(x_partition_fields, list) and len(x_partition_fields) > 0
        )
        schema = dict(self.schema)
        config = dict(self.config)
        if not hive:
            self._extraction_pattern = cast(
                BasePathPattern,
                SimplePath(
                    stream_name=self.stream_name,
                    config=config,
                    time_fn=self._time_fn,
                    storage_client=self._storage_client,
                    extraction_date=self._extraction_date,
                ),
            )
        elif has_partition_fields:
            self._extraction_pattern = cast(
                BasePathPattern,
                PartitionedPath(
                    stream_name=self.stream_name,
                    schema=schema,
                    config=config,
                    partition_fields=cast(list[str], x_partition_fields),
                    time_fn=self._time_fn,
                    storage_client=self._storage_client,
                    extraction_date=self._extraction_date,
                ),
            )
        else:
            self._extraction_pattern = cast(
                BasePathPattern,
                DatedPath(
                    stream_name=self.stream_name,
                    config=config,
                    time_fn=self._time_fn,
                    storage_client=self._storage_client,
                    extraction_date=self._extraction_date,
                ),
            )

    def process_record(self, record: dict, context: dict) -> None:
        """Process one record (RECORD message payload). Delegates to the selected extraction pattern."""
        self._extraction_pattern.process_record(record=record, context=context)

    def close(self) -> None:
        """Flush and close the pattern's write handle.

        Prefer :meth:`clean_up` in production paths: Singer SDK targets call
        ``clean_up`` at end-of-pipe, not ``close``.
        """
        self._extraction_pattern.close()

    def clean_up(self) -> None:
        """Finalize open GCS writes, then run RecordSink metric teardown.

        Singer SDK ``Target.drain_all(is_endofpipe=True)`` invokes ``clean_up``
        on each sink. Without closing the smart_open handle here, objects are
        never committed to GCS (records appear processed; bucket stays empty).
        """
        self.close()
        super().clean_up()

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

    def _parse_timestamps_in_record(
        self,
        record: dict,
        schema: dict,
        treatment: DatetimeErrorTreatmentEnum,
    ) -> None:
        """Parse date/time strings with dateutil so non-ISO formats (e.g. 'YYYY-MM-DD HH:MM:SS UTC') are accepted.

        Overrides SDK default (fromisoformat-only) to align with partition path parsing.
        Unparseable values are handled via handle_invalid_timestamp_in_record (per treatment).
        """
        for key, value in record.items():
            additional_properties = schema.get("additionalProperties", False)
            if key not in schema["properties"]:
                if (
                    value is not None
                    and not additional_properties
                    and key not in self._warned_missing_fields
                ):
                    self.logger.warning("No schema for record field '%s'", key)
                    self._warned_missing_fields.add(key)
                continue

            if datelike_type := get_datelike_property_type(schema["properties"][key]):
                date_val = value
                try:
                    if value is not None:
                        if datelike_type == "time":
                            date_val = time_fromisoformat(date_val)
                        elif datelike_type in ("date", "date-time"):
                            if isinstance(value, str):
                                parsed = dateutil_parser.parse(value)
                                date_val = (
                                    parsed.date() if datelike_type == "date" else parsed
                                )
                            else:
                                date_val = value
                        else:
                            date_val = value
                except (ValueError, DateutilParserError) as ex:
                    date_val = handle_invalid_timestamp_in_record(
                        record,
                        [key],
                        value,
                        datelike_type,
                        ex,
                        treatment,
                        self.logger,
                    )
                record[key] = date_val
