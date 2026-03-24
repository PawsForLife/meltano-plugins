# Usage

[← Examples](examples.md) · [Documentation index](index.md)


You can run `restful-api-tap` by itself or in a pipeline using [Meltano](www.meltano.com). The tap reads a **config file** and optionally a **catalog** and **state file** for incremental runs.

### Executing the Tap Directly

```bash
restful-api-tap --version
restful-api-tap --help
restful-api-tap --config CONFIG --discover > ./catalog.json
```

or

```bash
bash restful-api-tap --config=config.sample.json
```

## Developer documentation

See [Development guide](../docs/DEVELOPMENT.md) for local setup, tests, lint, and contributing.

[← Examples](examples.md) · [Documentation index](index.md)
