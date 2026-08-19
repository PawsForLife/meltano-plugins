# Changelog

## [Unreleased]

### Breaking

- Python 3.14 is now the minimum supported runtime; uv, Ruff, mypy, and local setup target 3.14.

## [0.2.1] - 2026-08-19

### Fixed

- **events-unsorted-created** — The `events` stream no longer claims the sorted-stream guarantee (`is_sorted = False`). The claim contradicted the stream's own resume design: runs with saved state rewind `createdAfter` by `lookback_minutes`, so the first record returned is older than the saved bookmark by construction, and the SDK raised `InvalidStreamSortException` on the first record of every resumed run. The SDK now tracks the maximum `created` bookmark across the run and finalizes state at stream completion; requests still ask for `sort=created` for stable offset pagination, but correctness no longer depends on the API honouring it. The `lookback_minutes` window plus downstream key-based dedup cover the boundary overlap, and a bookmark stuck by this bug self-heals on the first fixed run.
