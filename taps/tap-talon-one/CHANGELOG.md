# Changelog

## [Unreleased]

### Breaking

- Python 3.14 is now the minimum supported runtime; uv, Ruff, mypy, and local setup target 3.14.

## [0.2.1] - 2026-08-19

### Fixed

- **events-unsorted-created** — The `events` stream no longer claims the sorted-stream guarantee (`is_sorted = False`). Talon.One returns `created` timestamps slightly out of order even with `sort=created`, so every incremental run failed with `InvalidStreamSortException` at the first out-of-order record. The SDK now tracks the maximum `created` bookmark across the run and finalizes state at stream completion; requests still ask for `sort=created` for stable offset pagination, and the existing `lookback_minutes` window plus downstream key-based dedup cover boundary overlap.
