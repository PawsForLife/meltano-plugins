"""RecordSink implementation for the GCS target. Each sink handles one stream, receiving SCHEMA, RECORD, and STATE messages from the target and writing record data to the destination (GCS). The sink uses the config file for bucket and key settings. On close or when the target drains the sink (sink drain), buffered data is flushed to the destination."""

import time
from collections import defaultdict
from datetime import datetime
from io import FileIO
from typing import Callable, Optional

import orjson
import smart_open
from google.cloud.storage import Client
from singer_sdk.sinks import RecordSink


class GCSSink(RecordSink):
    """GCS sink implementing RecordSink (one record at a time). Handles one stream; writes records to the destination. Sink drain (flush/close) is performed when the sink is closed."""

    max_size = 1000  # Max records to write in one batch

    def __init__(
        self,
        target,
        stream_name,
        schema,
        key_properties,
        *,
        time_fn: Optional[Callable[[], float]] = None,
    ):
        super().__init__(
            target=target,
            stream_name=stream_name,
            schema=schema,
            key_properties=key_properties,
        )
        self._gcs_write_handle: Optional[FileIO] = None
        self._key_name: str = ""
        self._records_written_in_current_file: int = 0
        self._chunk_index: int = 0
        self._time_fn: Optional[Callable[[], float]] = time_fn

    @property
    def key_name(self) -> str:
        """Return the key name."""
        if not self._key_name:
            # Time is injectable via time_fn for deterministic key assertions in tests.
            extraction_timestamp = round((self._time_fn or time.time)())
            base_key_name = self.config.get(
                "key_naming_convention",
                f"{self.stream_name}_{extraction_timestamp}.{self.output_format}",
            )
            prefixed_key_name = (
                f"{self.config.get('key_prefix', '')}/{base_key_name}".replace(
                    "//", "/"
                )
            ).lstrip("/")
            date = datetime.today().strftime(self.config.get("date_format", "%Y-%m-%d"))
            self._key_name = prefixed_key_name.format_map(
                defaultdict(
                    str,
                    stream=self.stream_name,
                    date=date,
                    timestamp=extraction_timestamp,
                )
            )
        return self._key_name

    @property
    def gcs_write_handle(self) -> FileIO:
        """Opens a write handle for the destination (GCS object) for this stream."""
        if not self._gcs_write_handle:
            client = Client()
            self._gcs_write_handle = smart_open.open(
                f"gs://{self.config.get('bucket_name')}/{self.key_name}",
                "wb",
                transport_params={"client": client},
            )
        return self._gcs_write_handle

    @property
    def output_format(self) -> str:
        """In the future maybe we will support more formats"""
        return "jsonl"

    def process_record(self, record: dict, context: dict) -> None:
        """Process one record (RECORD message payload).

        Developers may optionally read or write additional markers within the
        passed `context` dict from the current batch.
        """
        self.gcs_write_handle.write(
            orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE)
        )
