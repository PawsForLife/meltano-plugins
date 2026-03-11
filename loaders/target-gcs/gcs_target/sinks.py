"""RecordSink implementation for the GCS target. Each sink handles one stream, receiving SCHEMA, RECORD, and STATE messages from the target and writing record data to the destination (GCS). The sink uses the config file for bucket and key settings. On close or when the target drains the sink (sink drain), buffered data is flushed to the destination."""

import time
from collections import defaultdict
from datetime import date, datetime
from io import FileIO
from typing import Callable, Optional

import orjson
import smart_open
from google.cloud.storage import Client
from singer_sdk.sinks import RecordSink

# Default Hive-style partition path format when partition_date_format is omitted by callers.
DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"


def get_partition_path_from_record(
    record: dict,
    partition_date_field: str,
    partition_date_format: str,
    fallback_date: datetime,
) -> str:
    """Resolve partition path string from the record's date field.

    Reads the record field named by partition_date_field. Parses as date/datetime
    (ISO via fromisoformat, then fallback %Y-%m-%d). If the field is missing or
    unparseable, returns fallback_date formatted with partition_date_format.
    Callers may use DEFAULT_PARTITION_DATE_FORMAT for Hive-style paths.

    Args:
        record: Record dict containing the partition date field.
        partition_date_field: Key in record for the date/datetime value.
        partition_date_format: strftime format for the returned path segment.
        fallback_date: Date used when field is missing or unparseable.

    Returns:
        Partition path string (e.g. "year=2024/month=03/day=11").
    """
    value = record.get(partition_date_field)
    if value is None:
        return fallback_date.strftime(partition_date_format)
    if isinstance(value, (datetime, date)):
        return value.strftime(partition_date_format)
    if not isinstance(value, str):
        return fallback_date.strftime(partition_date_format)
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime(partition_date_format)
    except (ValueError, TypeError):
        pass
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime(partition_date_format)
    except (ValueError, TypeError):
        pass
    return fallback_date.strftime(partition_date_format)


class GCSSink(RecordSink):
    """GCS sink implementing RecordSink (one record at a time). Handles one stream; writes records to the destination. Sink drain (flush/close) is performed when the sink is closed. When max_records_per_file is set, the sink rotates to a new file after that many records and uses current timestamp and chunk index in the key. When partition_date_field is set, the key is derived per record from that field; one active handle; on partition change the sink closes and clears state; when the partition \"returns,\" the next write creates a new key (new file)."""

    max_size = 1000  # Max records to write in one batch

    def __init__(
        self,
        target,
        stream_name,
        schema,
        key_properties,
        *,
        time_fn: Optional[Callable[[], float]] = None,
        date_fn: Optional[Callable[[], datetime]] = None,
    ):
        super().__init__(
            target=target,
            stream_name=stream_name,
            schema=schema,
            key_properties=key_properties,
        )
        self._gcs_write_handle: Optional[FileIO] = None
        self._key_name: str = ""
        self._records_written_in_current_file: int = (
            0  # Records written to current file; reset on rotation.
        )
        self._chunk_index: int = 0  # 0-based chunk index; incremented on rotation.
        self._time_fn: Optional[Callable[[], float]] = time_fn
        # Optional run-date callable for partition fallback and tests; default None → use datetime.today where needed.
        self._date_fn: Optional[Callable[[], datetime]] = date_fn
        if self.config.get("partition_date_field"):
            # Current partition path when partition-by-field is on; None when cleared or not yet set.
            self._current_partition_path: Optional[str] = None

    def _build_key_for_record(self, record: dict, partition_path: str) -> str:
        """Build the object key for a single record when partition_date_field is set.

        Uses key_prefix and key_naming_convention with format_map: stream,
        partition_date (= partition_path), timestamp (from _time_fn or time.time),
        and chunk_index when chunking is enabled. Same normalization as key_name
        (no double slashes, no leading slash). Callers pass a pre-resolved
        partition_path (e.g. from get_partition_path_from_record).

        Args:
            record: Record dict (unused; partition_path is pre-resolved).
            partition_path: Pre-resolved partition path segment (e.g. year=2024/month=03/day=11).

        Returns:
            Normalized key string for the GCS object.
        """
        extraction_timestamp = round((self._time_fn or time.time)())
        base_key_name = self.config.get(
            "key_naming_convention",
            f"{self.stream_name}_{extraction_timestamp}.{self.output_format}",
        )
        max_records = self.config.get("max_records_per_file", 0)
        format_map = defaultdict(
            str,
            stream=self.stream_name,
            partition_date=partition_path,
            timestamp=extraction_timestamp,
        )
        if max_records and max_records > 0:
            format_map["chunk_index"] = self._chunk_index
        base = base_key_name.format_map(format_map)
        prefixed = (
            f"{self.config.get('key_prefix', '')}/{base}".replace("//", "/")
        ).lstrip("/")
        return prefixed

    @property
    def key_name(self) -> str:
        """Return the key name. When partition_date_field is set, returns the current key after a write (or empty string); callers needing per-record keys use _build_key_for_record. When unset, recomputes from stream, date, timestamp and optionally chunk_index."""
        if self.config.get("partition_date_field"):
            return self._key_name
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
            run_date = self._date_fn() if self._date_fn else datetime.today()
            date = run_date.strftime(self.config.get("date_format", "%Y-%m-%d"))
            max_records = self.config.get("max_records_per_file", 0)
            format_map = defaultdict(
                str,
                stream=self.stream_name,
                date=date,
                timestamp=extraction_timestamp,
            )
            if max_records and max_records > 0:
                format_map["chunk_index"] = self._chunk_index
            self._key_name = prefixed_key_name.format_map(format_map)
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

    def _rotate_to_new_chunk(self) -> None:
        """Close the current file handle, clear key cache, increment chunk index, and reset record count. Used when record count reaches max_records_per_file before writing the next record. Flushes the handle before close when it supports flush (guarded so handles without flush do not raise)."""
        if self._gcs_write_handle is not None:
            if hasattr(self._gcs_write_handle, "flush"):
                self._gcs_write_handle.flush()
            self._gcs_write_handle.close()
            self._gcs_write_handle = None
        self._key_name = ""
        self._chunk_index += 1
        self._records_written_in_current_file = 0

    def _process_record_single_or_chunked(self, record: dict, context: dict) -> None:
        """Process one record when partition_date_field is unset (single-file or chunked by row limit).

        Assumes partition_date_field is unset. Rotates to a new chunk when
        max_records_per_file is set and record count has reached the limit;
        writes the record via gcs_write_handle; increments _records_written_in_current_file
        when chunking is enabled.
        """
        max_records = self.config.get("max_records_per_file", 0)
        if (
            max_records
            and max_records > 0
            and self._records_written_in_current_file >= max_records
        ):
            self._rotate_to_new_chunk()
        self.gcs_write_handle.write(
            orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE)
        )
        if max_records and max_records > 0:
            self._records_written_in_current_file += 1

    def _process_record_partition_by_field(self, record: dict, context: dict) -> None:
        """Process one record when partition_date_field is set (partition-by-field strategy).

        Assumes partition_date_field is set. Resolves partition path from record;
        on partition change closes handle and clears key/partition state and resets
        chunk index; rotates within partition when at max_records_per_file; builds
        key via _build_key_for_record; opens handle when none or key changed;
        writes record and increments count when chunking.
        """
        fallback = self._date_fn() if self._date_fn else datetime.today()
        partition_date_format = (
            self.config.get("partition_date_format") or DEFAULT_PARTITION_DATE_FORMAT
        )
        partition_path = get_partition_path_from_record(
            record,
            self.config["partition_date_field"],
            partition_date_format,
            fallback,
        )
        if partition_path != self._current_partition_path:
            if self._gcs_write_handle is not None:
                if hasattr(self._gcs_write_handle, "flush"):
                    self._gcs_write_handle.flush()
                self._gcs_write_handle.close()
                self._gcs_write_handle = None
            self._key_name = ""
            self._current_partition_path = partition_path
            self._chunk_index = 0
            self._records_written_in_current_file = 0
        max_records = self.config.get("max_records_per_file", 0)
        if (
            max_records
            and max_records > 0
            and self._records_written_in_current_file >= max_records
        ):
            self._rotate_to_new_chunk()
        key = self._build_key_for_record(record, partition_path)
        if self._gcs_write_handle is None or self._key_name != key:
            if self._gcs_write_handle is not None:
                if hasattr(self._gcs_write_handle, "flush"):
                    self._gcs_write_handle.flush()
                self._gcs_write_handle.close()
                self._gcs_write_handle = None
            self._key_name = key
            client = Client()
            self._gcs_write_handle = smart_open.open(
                f"gs://{self.config.get('bucket_name')}/{key}",
                "wb",
                transport_params={"client": client},
            )
        self._gcs_write_handle.write(
            orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE)
        )
        if max_records and max_records > 0:
            self._records_written_in_current_file += 1

    def process_record(self, record: dict, context: dict) -> None:
        """Process one record (RECORD message payload).

        When partition_date_field is set: delegates to _process_record_partition_by_field.
        When unset: delegates to _process_record_single_or_chunked (single key and
        handle, or chunking by max_records_per_file).
        """
        partition_date_field = self.config.get("partition_date_field")
        if not partition_date_field:
            self._process_record_single_or_chunked(record, context)
            return
        self._process_record_partition_by_field(record, context)
