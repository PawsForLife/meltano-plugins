# tap-talon-one

Singer SDK tap for full-refresh campaign extraction from the Talon.One Management API.

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
```

Do not set `variant` for this custom extractor. The tap supports Singer `--discover`, `--catalog`, and standard JSONL output for loaders such as `target-gcs`.

## Development

```bash
./install.sh
```
