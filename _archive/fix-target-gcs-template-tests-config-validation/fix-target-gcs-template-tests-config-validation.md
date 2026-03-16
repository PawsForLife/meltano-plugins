# Fix: target-gcs template tests config validation

## The request

Sixteen Singer SDK template tests for `GCSTarget` in `loaders/target-gcs/tests/test_core.py` failed with `ConfigValidationError: Config validation failed` during target construction. The test runner instantiates `GCSTarget(config=SAMPLE_CONFIG)`; `SAMPLE_CONFIG` was an empty dict while the target's JSON schema requires `bucket_name`. Other tests in the same package (e.g. `test_sinks.py`, `test_partition_key_generation.py`) already used a minimal config including `bucket_name` and passed.

## Planned approach

Root cause: empty `SAMPLE_CONFIG` in `test_core.py`. Fix: set `SAMPLE_CONFIG` to a minimal valid config so the runner can instantiate the target. Single task: set `SAMPLE_CONFIG = {"bucket_name": "test-bucket"}` and update the comment, matching the pattern used elsewhere in the loader tests. No schema or SDK changes.

## What was implemented

- **01-set-sample-config**: In `loaders/target-gcs/tests/test_core.py`, set `SAMPLE_CONFIG = {"bucket_name": "test-bucket"}` and replaced the TODO with a short comment. All 16 `TestGCSTarget` tests pass; CHANGELOG updated under `### Fixed` with a reference to this archive.
