"""Package of tests for GCSSink: key naming, config schema, chunking, partitioning, and GCS behaviour.

Tests are split into focused modules (test_key_naming, test_config_schema, test_chunking,
test_serialization, test_hive_validation, test_partitioning). Fixtures and RecordingGCSClient
are provided by tests/conftest.py; pytest discovers all test_* functions in this package.
"""
