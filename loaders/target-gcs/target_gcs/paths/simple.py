"""Simple path pattern: single path per stream, optional chunking by limit."""

from __future__ import annotations

from typing import Any

import smart_open

from target_gcs.paths.base import BasePathPattern

# Fallback when key_naming_convention is not in config (removed in task 03).
_DEFAULT_KEY_TEMPLATE = "{stream}_{timestamp}.{format}"


class SimplePath(BasePathPattern):
    """Non-hive-partitioned pattern: one path per stream, one handle, rotation at max_records_per_file with -{idx} in the key."""

    @property
    def key_template(self) -> str:
        return str(self.config.get("key_naming_convention", _DEFAULT_KEY_TEMPLATE))

    def _build_key(self) -> str:
        """Build current object key from template and format map (stream, date, timestamp, format, optional chunk_index)."""
        fmt = self.get_chunk_format_map()
        base = self.key_template.format(**fmt)
        return self.apply_key_prefix_and_normalize(base)

    def process_record(self, record: dict[str, Any], context: dict[str, Any]) -> None:
        """Rotate if at limit, ensure handle open, write record as JSONL, and set current key."""
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
