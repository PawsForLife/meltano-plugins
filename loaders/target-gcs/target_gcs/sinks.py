"""RecordSink implementation for the GCS target. Each sink handles one stream, receiving SCHEMA, RECORD, and STATE messages from the target and writing record data to the destination (GCS). The sink uses the config file for bucket and key settings. On close or when the target drains the sink (sink drain), buffered data is flushed to the destination."""

import time
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from io import FileIO
from typing import Any

import orjson
import smart_open
from dateutil.parser import ParserError
from google.cloud.storage import Client
from singer_sdk.sinks import RecordSink

from .helpers import (
    _json_default,
    get_partition_path_from_schema_and_record,
    validate_partition_fields_schema,
)
from .helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT

# Default key template when hive_partitioned is false.
DEFAULT_KEY_NAMING_CONVENTION = "{stream}_{timestamp}.{format}"
# Default key template when hive_partitioned is true and key_naming_convention omitted.
DEFAULT_KEY_NAMING_CONVENTION_HIVE = "{stream}/{partition_date}/{timestamp}.{format}"


class GCSSink(RecordSink):
    """GCS sink implementing RecordSink (one record at a time). Handles one stream; writes records to the destination. Sink drain (flush/close) is performed when the sink is closed. When max_records_per_file is set, the sink rotates to a new file after that many records and uses current timestamp and chunk index in the key. When hive_partitioned is true, the key is derived per record from x-partition-fields (or extraction date when absent); one active handle; on partition change the sink closes and clears state; when the partition \"returns,\" the next write creates a new key (new file)."""

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
        self._gcs_write_handle: FileIO | None = None
        self._key_name: str = ""
        self._records_written_in_current_file: int = (
            0  # Records written to current file; reset on rotation.
        )
        self._chunk_index: int = 0  # 0-based chunk index; incremented on rotation.
        self._current_timestamp: int | None = (
            None  # Cached at handle open; used for key building.
        )
        self._time_fn: Callable[[], float] | None = time_fn
        # Optional run-date callable for partition extraction date and tests; default None → use datetime.today where needed.
        self._date_fn: Callable[[], datetime] | None = date_fn
        self._extraction_date = self._date_fn() if self._date_fn else datetime.today()

        self._storage_client: Any | None = storage_client

        if self.config.get("hive_partitioned"):
            # Current partition path when Hive partitioning is on; None when cleared or not yet set.
            self._current_partition_path: str | None = None
            x_partition_fields = self.schema.get("x-partition-fields")
            if isinstance(x_partition_fields, list) and len(x_partition_fields) > 0:
                validate_partition_fields_schema(
                    self.stream_name,
                    self.schema,
                    x_partition_fields,
                )

    def _get_effective_key_template(self) -> str:
        """Return the key template to use: user override, hive default, or non-partition default.

        Rule: (1) If key_naming_convention is set and non-empty, return it. (2) Else if
        hive_partitioned is true, return DEFAULT_KEY_NAMING_CONVENTION_HIVE. (3) Else
        return DEFAULT_KEY_NAMING_CONVENTION.
        """
        user_template = (self.config.get("key_naming_convention") or "").strip()
        if user_template:
            return user_template
        if self.config.get("hive_partitioned"):
            return DEFAULT_KEY_NAMING_CONVENTION_HIVE
        return DEFAULT_KEY_NAMING_CONVENTION

    def _apply_key_prefix_and_normalize(self, base: str) -> str:
        """Apply config key_prefix to the base path and normalize slashes.

        Joins key_prefix (or empty string if unset) with base, collapses repeated
        slashes, and strips leading slash so the key never starts with /.

        Args:
            base: Path segment to prefix and normalize (e.g. stream/partition/timestamp.jsonl).

        Returns:
            Normalized key string (no leading slash, no double slashes).
        """
        prefix = self.config.get("key_prefix", "") or ""
        return f"{prefix}/{base}".replace("//", "/").lstrip("/")

    def _build_key_for_record(self, record: dict, partition_path: str) -> str:
        """Build the object key for a single record when hive_partitioned is true.

        Uses key_prefix and the effective key template (from _get_effective_key_template)
        with format_map: stream, partition_date (= partition_path), hive (= partition_path,
        alias for partition_date), timestamp (from _time_fn or time.time), and chunk_index
        when chunking is enabled. If the template contains {format}, format_map includes
        format=self.output_format. Same normalization as key_name (no double slashes,
        no leading slash). Callers pass a pre-resolved partition_path (e.g. from
        get_partition_path_from_schema_and_record).

        Args:
            record: Record dict (unused; partition_path is pre-resolved).
            partition_path: Pre-resolved partition path segment (e.g. year=2024/month=03/day=11).

        Returns:
            Normalized key string for the GCS object.
        """
        if self._current_timestamp is None:
            self._current_timestamp = round((self._time_fn or time.time)())

        extraction_timestamp = self._current_timestamp
        base_key_name = self._get_effective_key_template()
        max_records = self.config.get("max_records_per_file", 0)
        format_map = defaultdict(
            str,
            stream=self.stream_name,
            partition_date=partition_path,
            hive=partition_path,
            timestamp=extraction_timestamp,
        )
        if max_records and max_records > 0:
            format_map["chunk_index"] = self._chunk_index
        if "{format}" in base_key_name:
            format_map["format"] = self.output_format
        base = base_key_name.format_map(format_map)
        return self._apply_key_prefix_and_normalize(base)

    @property
    def storage_client(self) -> Client:
        if self._storage_client is None:
            self._storage_client = Client()
        return self._storage_client

    @property
    def key_name(self) -> str:
        """Return the key name. When hive_partitioned is true, returns the current key after a write (or empty string); callers needing per-record keys use _build_key_for_record. When false, computes key from the same effective template as _build_key_for_record (_get_effective_key_template), then format_map (stream, date, timestamp, format, and optionally chunk_index). Default when key_naming_convention is omitted is DEFAULT_KEY_NAMING_CONVENTION."""
        if self.config.get("hive_partitioned"):
            return self._key_name
        if not self._key_name:
            # Time is injectable via time_fn for deterministic key assertions in tests.
            extraction_timestamp = round((self._time_fn or time.time)())
            base_key_name = self._get_effective_key_template()
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
                format=self.output_format,
            )
            if max_records and max_records > 0:
                format_map["chunk_index"] = self._chunk_index
            self._key_name = prefixed_key_name.format_map(format_map)
        return self._key_name

    @property
    def gcs_write_handle(self) -> FileIO:
        """Opens a write handle for the destination (GCS object) for this stream."""
        if not self._gcs_write_handle:
            self._gcs_write_handle = smart_open.open(
                f"gs://{self.config.get('bucket_name')}/{self.key_name}",
                "wb",
                transport_params={"client": self.storage_client},
            )
        return self._gcs_write_handle

    def _flush_and_close_handle(self) -> None:
        """Flush and close the current GCS write handle and set it to None. Safe when handle has no flush attribute."""
        if self._gcs_write_handle is not None:
            if hasattr(self._gcs_write_handle, "flush"):
                self._gcs_write_handle.flush()
            self._gcs_write_handle.close()
            self._gcs_write_handle = None

    @property
    def output_format(self) -> str:
        """In the future maybe we will support more formats"""
        return "jsonl"

    def _rotate_to_new_chunk(self) -> None:
        """Close the current file handle, clear key cache, increment chunk index, reset record count, and refresh cached timestamp for key generation. Used when record count reaches max_records_per_file before writing the next record. Flushes the handle before close when it supports flush (guarded so handles without flush do not raise)."""
        self._flush_and_close_handle()
        self._key_name = ""
        self._chunk_index += 1
        self._records_written_in_current_file = 0
        self._current_timestamp = round((self._time_fn or time.time)())

    def _close_handle_and_clear_state(self) -> None:
        """Close the current GCS write handle and clear key state. If a handle is open, flushes (if supported), closes it, and sets _gcs_write_handle to None; then sets _key_name to empty string and _current_timestamp to None so the next open gets a fresh timestamp. Does not modify _current_partition_path, _chunk_index, or _records_written_in_current_file; the caller updates those when appropriate."""
        self._flush_and_close_handle()
        self._key_name = ""
        self._current_timestamp = None

    def _write_record_as_jsonl(self, record: dict) -> None:
        """Write a single record as a JSONL line to the current GCS write handle.

        Serializes the record with orjson (OPT_APPEND_NEWLINE, _json_default for
        non-JSON-serializable values) and writes the result to gcs_write_handle.

        Args:
            record: Record dict to serialize and write.
        """
        self.gcs_write_handle.write(
            orjson.dumps(
                record,
                option=orjson.OPT_APPEND_NEWLINE,
                default=_json_default,
            )
        )

    def _process_record_single_or_chunked(self, record: dict, context: dict) -> None:
        """Process one record when hive_partitioned is false (single-file or chunked by row limit).

        Assumes hive_partitioned is false. Rotates to a new chunk when
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
        self._write_record_as_jsonl(record)
        if max_records and max_records > 0:
            self._records_written_in_current_file += 1

    def _process_record_hive_partitioned(self, record: dict, context: dict) -> None:
        """Process one record when hive_partitioned is true (schema-driven Hive path).

        Assumes hive_partitioned is true. Partition path comes from
        get_partition_path_from_schema_and_record(schema, record, extraction_date,
        partition_date_format=DEFAULT_PARTITION_DATE_FORMAT). On partition change closes
        handle and clears key/partition state and resets chunk index; rotates within
        partition when at max_records_per_file; builds key via _build_key_for_record;
        opens handle when none or key changed; writes record and increments count when
        chunking. Re-raises ParserError from path builder on unparseable date.
        """
        try:
            partition_path = get_partition_path_from_schema_and_record(
                self.schema,
                record,
                extraction_date=self._extraction_date,
                partition_date_format=DEFAULT_PARTITION_DATE_FORMAT,
            )
        except ParserError:
            # Unparseable partition date string: re-raise so the run fails visibly.
            raise
        if partition_path != self._current_partition_path:
            self._close_handle_and_clear_state()
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
            self._close_handle_and_clear_state()
            self._key_name = key
            self._gcs_write_handle = smart_open.open(
                f"gs://{self.config.get('bucket_name')}/{key}",
                "wb",
                transport_params={"client": self.storage_client},
            )
        self._write_record_as_jsonl(record)
        if max_records and max_records > 0:
            self._records_written_in_current_file += 1

    def process_record(self, record: dict, context: dict) -> None:
        """Process one record (RECORD message payload).

        Dispatches by hive_partitioned: when true, partition-by-schema path
        (per-record partition from x-partition-fields or extraction date, handle
        lifecycle on partition/key change); when false, single-file or chunked path
        (one key/handle per stream per run, optional rotation by max_records_per_file).
        """
        if self.config.get("hive_partitioned"):
            self._process_record_hive_partitioned(record, context)
        else:
            self._process_record_single_or_chunked(record, context)
