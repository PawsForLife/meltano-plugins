"""Base path pattern for GCS: key prefix, template, and write/rotation stubs.

Shared by Simple, Dated, and Partitioned path patterns; GCSSink will delegate to a pattern
after refactor. Do not import from target_gcs.sinks to avoid circular dependency.
"""

from __future__ import annotations

import abc
import contextlib
from collections.abc import Callable
from datetime import datetime
from io import FileIO
from typing import Any

# Default key template when hive_partitioned is false.
DEFAULT_KEY_NAMING_CONVENTION = "{stream}_{timestamp}.{format}"
# Default key template when hive_partitioned is true and key_naming_convention omitted.
DEFAULT_KEY_NAMING_CONVENTION_HIVE = "{stream}/{partition_date}/{timestamp}.{format}"


class BasePathPattern(abc.ABC):
    """Abstract base for path patterns: key prefix, template, and write/rotation hooks.

    Subclasses implement process_record and close; base provides key prefix normalization,
    effective key template resolution, and stub/minimal write/rotation/flush/chunk-format
    helpers (fully implemented in a later task).
    """

    def __init__(
        self,
        target: Any,
        stream_name: str,
        schema: dict[str, Any],
        key_properties: list[str],
        config: dict[str, Any],
        *,
        time_fn: Callable[[], float] | None = None,
        date_fn: Callable[[], datetime] | None = None,
        storage_client: Any | None = None,
        extraction_date: datetime | None = None,
    ) -> None:
        self.target = target
        self.stream_name = stream_name
        self.schema = schema
        self.key_properties = key_properties
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

    def get_effective_key_template(self) -> str:
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

    @property
    def current_key(self) -> str:
        """Current object key (e.g. after a write); empty until set by subclass."""
        return self._key_name

    @abc.abstractmethod
    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Process one record; subclass writes to GCS or buffers."""
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """Flush and release resources; subclass must implement."""
        ...

    def write_record_as_jsonl(self, record: dict[str, Any]) -> None:  # noqa: B027
        """Write record as one JSONL line. Stub; full implementation in a later task."""
        pass

    def maybe_rotate_if_at_limit(self) -> None:  # noqa: B027
        """Rotate to new chunk if record limit reached. Stub; full implementation in a later task."""
        pass

    def flush_and_close_handle(self) -> None:
        """Flush and close the current write handle; set _current_handle to None."""
        if self._current_handle is not None:
            with contextlib.suppress(OSError):
                self._current_handle.flush()
            with contextlib.suppress(OSError):
                self._current_handle.close()
            self._current_handle = None

    def get_chunk_format_map(self) -> dict[str, Any]:
        """Return format map for key template (stream, timestamp, format, chunk_index, etc.). Minimal stub."""
        return {
            "stream": self.stream_name,
            "timestamp": self._current_timestamp or 0,
            "format": "jsonl",
            "chunk_index": self._chunk_index,
        }
