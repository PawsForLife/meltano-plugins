# Talon.One Management API integration: campaigns and events extraction

**Scope:** `tap-talon-one`, Python 3.12, Talon.One Management API campaigns and application events.

**Bottom line:** The tap matches Talon.One's documented authentication, endpoints, response envelopes, pagination, and filtering contract. The Management API is limited to three requests per second per endpoint, so the tap relies on Singer SDK retries and Talon.One's `Retry-After` response when throttled.

## 1. Prerequisites and install

- A Talon.One Management API key permitted to read campaigns and application events.
- The Talon.One deployment base URL and Application ID.
- Python 3.12 or later.

```bash
pip install "git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/tap-talon-one"
```

## 2. Authentication and configuration

Every request sends `Authorization: ManagementKey-v1 <key>` over HTTPS. `api_url`, `management_key`, and `application_id` are required. `start_date` is required only when the events stream has no Singer bookmark; a matching stored bookmark takes precedence on resumed runs.

## 3. Minimal working example

```yaml
plugins:
  extractors:
    - name: tap-talon-one
      namespace: tap_talon_one
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/tap-talon-one
      config:
        api_url: ${TALON_ONE_API_URL}
        management_key: ${TALON_ONE_KEY}
        application_id: ${TALON_ONE_APPLICATION_ID}
        start_date: 2026-07-01T00:00:00Z
        lookback_minutes: 5
```

## 4. Core API surface

- `GET /v1/applications/{applicationId}/campaigns`: full-table campaigns with `pageSize`, `skip`, and stable `sort`.
- `GET /v1/applications/{applicationId}/events/no_total`: incremental events with `createdAfter`, `pageSize`, `skip`, and stable `sort`.
- Campaign responses use `totalResultSize` and `data`; the no-total events response uses `hasMore` and `data`.
- `pageSize` accepts 1 through 1000. Talon.One accepts RFC3339 timestamps and converts supplied time zones to UTC.

## 5. Gotchas

- `createdAfter` means strictly after the timestamp. The configurable lookback intentionally rereads a boundary window for downstream key-based deduplication.
- The Singer SDK normally chooses the newer of configured `start_date` and stored state. This tap reads a matching bookmark first because DNA-9422 requires state to remain authoritative after the first run.
- No relevant independent community reports were found for these two endpoints; the contract is corroborated by Talon.One's reference, Postman collection, generated Python SDK, and credentialed project smoke tests.

## 6. Limitations

- The Management API is for back-office work, not real-time customer-facing traffic.
- This tap intentionally exposes only campaigns and events.
- It does not deduplicate records reread by the overlap window.

## 7. Sources

### Official documentation

- [Management API reference](https://docs.talon.one/management-api)
- [Management API overview](https://docs.talon.one/docs/dev/management-api/overview)
- [Official Postman collection](https://gist.githubusercontent.com/talononebot/e3d16bd2e49bcc7550cead99628748ff/raw/66ebe79cab6a76aff740b664f2d31c11ba5c375c/management-api.json)

### Real code

- [Talon.One Python SDK 12.0.0: application events endpoint](https://github.com/talon-one/talon_one.py/blob/12.0.0/talon_one/api/management_api.py#L9593-L9840)
- [Merged campaigns implementation and smoke test](https://github.com/PawsForLife/meltano-plugins/pull/16)
- [Merged incremental events implementation and smoke test](https://github.com/PawsForLife/meltano-plugins/pull/17)

### Community

No endpoint-specific community source was found; this source tier is degraded.
