# restful-api-tap — documentation index

User-facing documentation for the tap. Each file is kept within the repository Markdown line limit (500 lines).

| File | Reference | Description |
|------|-----------|-------------|
| [overview.md](overview.md) | `./README/overview.md` | Fork notice, capabilities, authentication overview, memory/performance notes, acknowledgements. |
| [installation.md](installation.md) | `./README/installation.md` | Install from monorepo, generic Meltano `meltano.yml` settings list, `meltano install`. |
| [configuration.md](configuration.md) | `./README/configuration.md` | Top-level and stream-level config, authentication options, complex auth patterns. |
| [pagination.md](pagination.md) | `./README/pagination.md` | Request/response pagination styles, JSONPath tokens, `pagination_stop_on_duplicate_token`, examples. |
| [examples.md](examples.md) | `./README/examples.md` | Environment-variable examples for Graph, GitLab, GitHub, FHIR, NOAA, dbt Cloud, OpenSearch. |
| [usage.md](usage.md) | `./README/usage.md` | Running the tap from the CLI and developer documentation link. |

Start with [overview.md](overview.md) or [installation.md](installation.md) if you are wiring the tap into Meltano.
