# Archive: ADC default, credentials via environment only

## The request

The target was to use Application Default Credentials (ADC) by default and to stop supporting a credentials file path in config. When users need a credentials file, they must set `GOOGLE_APPLICATION_CREDENTIALS`; the target must not read or accept a credentials path from config. Testing had to assert schema has no `credentials_file`, client is created without an explicit path (ADC), and behaviour when `GOOGLE_APPLICATION_CREDENTIALS` is set.

## Planned approach

Research and plan chose a single code path: always construct `google.cloud.storage.Client()` with no arguments so credentials come only from ADC (which honours `GOOGLE_APPLICATION_CREDENTIALS`). Remove `credentials_file` from config schema, sink, Meltano settings, sample config, and README. Tasks: (1) TDD tests first, (2) remove from schema, (3) sink always `Client()`, (4) update meltano.yml and sample.config.json, (5) README config table and Authentication section. Breaking change documented in README.

## What was implemented

- **Config**: Removed `credentials_file` from `config_jsonschema` in `target_gcs/target.py`.
- **Sink**: In `target_gcs/sinks.py`, `gcs_write_handle` always uses `Client()`; removed credentials_path and `from_service_account_json` branch.
- **Tests**: Updated `build_sink` default_config (no `credentials_file`), removed debug prints; added `test_config_schema_has_no_credentials_file`, `test_gcs_client_created_without_credentials_path`, `test_gcs_client_uses_adc_when_google_application_credentials_set`.
- **Artifacts**: Removed `credentials_file` from `meltano.yml` (settings and config) and `sample.config.json`.
- **Docs**: README config table no longer lists credentials_file; added Authentication subsection (ADC by default, credentials file only via `GOOGLE_APPLICATION_CREDENTIALS`).

All 12 tests pass. Breaking change: users who previously set a credentials path in config must use `GOOGLE_APPLICATION_CREDENTIALS` instead.
