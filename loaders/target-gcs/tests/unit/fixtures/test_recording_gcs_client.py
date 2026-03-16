"""Unit tests for RecordingGCSClient.

Validates that the recording client stores written bytes, records paths,
and satisfies the interface used by smart_open's GCS backend (get_blob, blob, open).
Black-box: assert on get_written_content and get_written_paths only.
"""

from __future__ import annotations

from tests.fixtures.recording_gcs_client import (
    RecordingGCSClient,
)


def test_write_then_read_returns_same_bytes() -> None:
    """WHAT: Data written via blob.open('wb') and closed is readable via get_blob().open('rb').
    WHY: Ensures the recording client persists bytes keyed by (bucket, key) and read path works."""
    client = RecordingGCSClient()
    bucket = client.bucket("b1")
    blob = bucket.blob("k1", chunk_size=1024)
    handle = blob.open("wb")
    payload = b"hello world"
    handle.write(payload)
    handle.close()
    got = client.bucket("b1").get_blob("k1")
    assert got is not None
    read_handle = got.open("rb")
    assert read_handle.read() == payload
    read_handle.close()


def test_multiple_blobs_and_buckets_stored_correctly() -> None:
    """WHAT: Writes to (bucket1, key1), (bucket1, key2), (bucket2, key1) are each retrievable.
    WHY: Ensures store is keyed by (bucket, key) and get_written_content returns correct bytes."""
    client = RecordingGCSClient()
    for bucket_name, key, content in [
        ("bucket1", "key1", b"a"),
        ("bucket1", "key2", b"b"),
        ("bucket2", "key1", b"c"),
    ]:
        blob = client.bucket(bucket_name).blob(key)
        h = blob.open("wb")
        h.write(content)
        h.close()
    assert client.get_written_content("bucket1", "key1") == b"a"
    assert client.get_written_content("bucket1", "key2") == b"b"
    assert client.get_written_content("bucket2", "key1") == b"c"


def test_get_written_paths_returns_order_of_first_write_open() -> None:
    """WHAT: get_written_paths() returns (bucket, key) list in order of first write-open (commit).
    WHY: Tests can assert on which paths were used without parsing mock call args."""
    client = RecordingGCSClient()
    b1 = client.bucket("b1")
    b2 = client.bucket("b2")
    h1 = b1.blob("k1").open("wb")
    h1.write(b"1")
    h1.close()
    h2 = b2.blob("k2").open("wb")
    h2.write(b"2")
    h2.close()
    h3 = b1.blob("k3").open("wb")
    h3.write(b"3")
    h3.close()
    paths = client.get_written_paths()
    assert paths == [("b1", "k1"), ("b2", "k2"), ("b1", "k3")]


def test_get_blob_returns_none_for_never_written_key() -> None:
    """WHAT: get_blob(key) returns None when (bucket, key) was never written.
    WHY: smart_open's Reader expects None for missing blobs and raises NotFound."""
    client = RecordingGCSClient()
    bucket = client.bucket("b1")
    assert bucket.get_blob("nonexistent") is None
    assert client.get_written_content("b1", "nonexistent") is None


def test_blob_setattr_allowed_then_write_persists() -> None:
    """WHAT: setattr on blob (e.g. content_type) does not error; write still persists and is readable.
    WHY: smart_open's Writer sets blob properties via setattr; mock must allow it and still commit."""
    client = RecordingGCSClient()
    bucket = client.bucket("b1")
    blob = bucket.blob("k1")
    blob.content_type = "application/json"
    handle = blob.open("wb")
    handle.write(b"data")
    handle.close()
    assert client.get_written_content("b1", "k1") == b"data"
