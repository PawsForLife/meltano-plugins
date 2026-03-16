"""Recording mock GCS client for tests.

Implements the interface used by smart_open's GCS backend so tests can pass
it via transport_params={"client": ...} and assert on stored content and paths
without patching smart_open. For test use only.
"""

from __future__ import annotations

import io
from typing import IO, Any

# In-memory store: (bucket_name, key) -> blob bytes.
# Write-open order recorded for get_written_paths().
# Shared by all buckets/blobs from this client.


class RecordingBlob:
    """Blob-like object that reads/writes to the client store and records paths on write."""

    def __init__(
        self,
        bucket_name: str,
        key: str,
        store: dict[tuple[str, str], bytes],
        written_paths: list[tuple[str, str]],
        *,
        for_write: bool = False,
    ) -> None:
        self._bucket_name = bucket_name
        self._key = key
        self._store = store
        self._written_paths = written_paths
        self._for_write = for_write

    def open(self, mode: str, **kwargs: Any) -> IO[bytes]:
        """Return a file-like for reading or writing. Write path commits on flush/close."""
        if mode == "rb":
            data = self._store.get((self._bucket_name, self._key))
            if data is None:
                raise FileNotFoundError(
                    f"blob {self._key} not found in {self._bucket_name}"
                )
            return io.BytesIO(data)
        if mode == "wb":
            bucket_name = self._bucket_name
            key = self._key
            store = self._store
            written_paths = self._written_paths

            class Writer(io.BytesIO):
                def close(self) -> None:
                    self.flush()
                    io.BytesIO.close(self)

                def flush(self) -> None:
                    if getattr(self, "_committed", False):
                        return
                    self.seek(0)
                    content = self.read()
                    store[(bucket_name, key)] = content
                    path = (bucket_name, key)
                    if path not in written_paths:
                        written_paths.append(path)
                    self._committed = True

            writer = Writer()
            writer._committed = False
            return writer
        raise ValueError(f"unsupported mode: {mode}")


class RecordingBucket:
    """Bucket-like object that returns RecordingBlobs backed by the client store."""

    def __init__(
        self,
        bucket_name: str,
        store: dict[tuple[str, str], bytes],
        written_paths: list[tuple[str, str]],
    ) -> None:
        self._bucket_name = bucket_name
        self._store = store
        self._written_paths = written_paths

    def get_blob(self, key: str, **kwargs: Any) -> RecordingBlob | None:
        """Return a blob if (bucket, key) exists in the store, else None."""
        if (self._bucket_name, key) not in self._store:
            return None
        return RecordingBlob(
            self._bucket_name,
            key,
            self._store,
            self._written_paths,
            for_write=False,
        )

    def blob(
        self,
        blob_name: str,
        chunk_size: int | None = None,
        **kwargs: Any,
    ) -> RecordingBlob:
        """Return a blob for writing; data is committed on flush/close of the opened handle."""
        return RecordingBlob(
            self._bucket_name,
            blob_name,
            self._store,
            self._written_paths,
            for_write=True,
        )


class RecordingGCSClient:
    """In-memory GCS client that records written content and paths for tests."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], bytes] = {}
        self._written_paths: list[tuple[str, str]] = []
        self._buckets: dict[str, RecordingBucket] = {}

    def bucket(self, name: str) -> RecordingBucket:
        """Return a RecordingBucket for the given name (created if needed)."""
        if name not in self._buckets:
            self._buckets[name] = RecordingBucket(
                name, self._store, self._written_paths
            )
        return self._buckets[name]

    def get_written_content(self, bucket: str, key: str) -> bytes | None:
        """Return bytes stored for (bucket, key), or None if never written."""
        return self._store.get((bucket, key))

    def get_written_paths(self) -> list[tuple[str, str]]:
        """Return (bucket_name, key) list in order of first write-open."""
        return list(self._written_paths)
