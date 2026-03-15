"""Shared test helpers for target-gcs tests.

Path tests and test_sinks import key_from_open_call from here (used when refactoring).
"""

from __future__ import annotations


def key_from_open_call(call_args: tuple) -> str:
    """Extract the GCS object key from smart_open.open positional-args tuple.

    Args:
        call_args: The positional-args tuple of a smart_open.open call (e.g.
            mock_open.call_args[0]). First element must be the GCS URI (gs://bucket/key).

    Returns:
        The key part after gs://bucket/ (e.g. gs://bucket/path/to/key -> path/to/key).
        Trailing slashes are preserved (e.g. gs://bucket/foo/ -> foo/).
    """
    url: str = str(call_args[0])
    return url.split("/", 3)[-1]
