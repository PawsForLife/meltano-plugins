"""Base path pattern for GCS: key prefix, template, and write/rotation.

Shared by Simple, Dated, and Partitioned path patterns; GCSSink will delegate to a pattern
after refactor. Do not import from target_gcs.sinks to avoid circular dependency.
"""

from __future__ import annotations

import abc
import time
from collections.abc import Callable
from datetime import datetime
from io import FileIO
from typing import Any

import orjson
from google.cloud.storage import Client

from target_gcs.helpers import _json_default


class BasePathPattern(abc.ABC):
    """Abstract base for path patterns: key prefix, template, and write/rotation hooks.

    Subclasses implement process_record and close; base provides key prefix normalization,
    effective key template resolution, and stub/minimal write/rotation/flush/chunk-format
    helpers (fully implemented in a later task).
    """

    max_size = 1000

    def __init__(
        self,
        stream_name: str,
        config: dict[str, Any],
        *,
        time_fn: Callable[[], float] | None = None,
        date_fn: Callable[[], datetime] | None = None,
        storage_client: Any | None = None,
        extraction_date: datetime | None = None,
    ) -> None:
        self.stream_name = stream_name
        self.config = config
        self._time_fn = time_fn
        self._date_fn = date_fn
        self._storage_client = storage_client
        self._extraction_date = extraction_date or (
            date_fn() if date_fn else datetime.today()
        )
        self._current_handle: FileIO | None = None
        self._key_name: str = ""
        self._chunk_index: int = 0
        self._records_written_in_current_file: int = 0
        self._current_timestamp: int | None = None
        self.bucket_name: str = config.get("bucket_name", "") or ""

    @property
    def storage_client(self) -> Client:
        """Resolved storage client; creates default Client when not injected."""
        if self._storage_client is None:
            self._storage_client = Client()
        return self._storage_client

    def apply_key_prefix_and_normalize(self, base: str) -> str:
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

    @property
    def current_key(self) -> str:
        """Current object key (e.g. after a write); empty until set by subclass."""
        return self._key_name

    @property
    @abc.abstractmethod
    def key_template(self) -> str:
        """Template string for generating path key"""
        ...

    @abc.abstractmethod
    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Process one record; subclass writes to GCS or buffers."""
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """Flush and release resources; subclass must implement."""
        ...

    def write_record_as_jsonl(self, record: dict[str, Any]) -> None:
        """Write record as one JSONL line to _current_handle.

        Serializes with orjson (OPT_APPEND_NEWLINE, _json_default for Decimal).
        Caller must set _current_handle to an open handle before calling.

        Args:
            record: Record dict to serialize and write.
        """
        if self._current_handle is None:
            return
        self._current_handle.write(
            orjson.dumps(
                record,
                option=orjson.OPT_APPEND_NEWLINE,
                default=_json_default,
            )
        )
        self._records_written_in_current_file += 1

    def maybe_rotate_if_at_limit(self) -> None:
        """Rotate to new chunk when max_records_per_file is reached.

        When max_records_per_file > 0 and _records_written_in_current_file >= limit,
        flushes and closes the handle, increments _chunk_index, resets record count,
        and refreshes _current_timestamp. No-op when max_records_per_file is 0 or missing.
        """
        max_records = self.config.get("max_records_per_file", 0)
        if max_records <= 0:
            return
        if self._records_written_in_current_file < max_records:
            return
        self.flush_and_close_handle()
        self._chunk_index += 1
        self._records_written_in_current_file = 0
        time_fn = self._time_fn or time.time
        self._current_timestamp = round(time_fn())

    def flush_and_close_handle(self) -> None:
        """Flush and close the current write handle; set _current_handle to None.

        Safe when handle has no flush attribute (only flush if hasattr).
        """
        if self._current_handle is not None:
            if hasattr(self._current_handle, "flush"):
                self._current_handle.flush()
            self._current_handle.close()
            self._current_handle = None

    def get_chunk_format_map(self) -> dict[str, Any]:
        """Return format map for key template: stream, date, timestamp, format; chunk_index when chunking."""
        date_fmt = self.config.get("date_format", "%Y-%m-%d")
        date_val = self._extraction_date.strftime(date_fmt)
        time_fn = self._time_fn or time.time
        ts = round(time_fn())
        out: dict[str, Any] = {
            "stream": self.stream_name,
            "date": date_val,
            "timestamp": ts,
            "format": "jsonl",
        }
        if self.config.get("max_records_per_file", 0) > 0:
            out["chunk_index"] = self._chunk_index
        return out
