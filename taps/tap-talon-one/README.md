# tap-talon-one

Singer SDK tap for campaign, incremental event, and application config/reference extraction from the Talon.One Management API.

Streams: `application` (singleton), `campaigns`, `cart_item_filters`, `events` (incremental), `event_types`. All streams except `events` are full-table.

## Meltano

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
        page_size: 1000
        start_date: 2026-07-01T00:00:00Z
        lookback_minutes: 5
```

Do not set `variant` for this custom extractor. The tap supports Singer `--discover`, `--catalog`, and standard JSONL output for loaders such as `target-gcs`.

The events stream resumes from its `created` Singer bookmark. On resumed runs, `lookback_minutes` rereads a small boundary window; downstream loaders should deduplicate those records by event `id`.
`start_date` is only required for the first events sync; an existing Singer bookmark remains authoritative on resumed runs.

## Development

```bash
./install.sh
```
