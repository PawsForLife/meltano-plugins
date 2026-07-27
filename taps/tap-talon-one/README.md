# tap-talon-one

Singer SDK tap for the Talon.One Management API. Extracts campaigns (full table),
application events (incremental), and triggered effects (full table over a rolling
window).

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
        effects_window_minutes: 1500
```

Do not set `variant` for this custom extractor. The tap supports Singer `--discover`, `--catalog`, and standard JSONL output for loaders such as `target-gcs`.

The events stream resumes from its `created` Singer bookmark. On resumed runs, `lookback_minutes` rereads a small boundary window; downstream loaders should deduplicate those records by event `id`.
`start_date` is only required for the first events sync; an existing Singer bookmark remains authoritative on resumed runs.

The `export_effects` stream reads the Analytics effects export, which Talon.One returns as CSV. It has no per-row cursor, so it is full table over a rolling window: each run requests `[now - effects_window_minutes, now]` (frozen at run start) and emits one JSON record per CSV row. Runs overlap by design; downstream loaders deduplicate. `effects_window_minutes` defaults to 1500 (25 hours) so a daily schedule keeps a margin across daylight-saving changes.

## Development

```bash
./install.sh
```
