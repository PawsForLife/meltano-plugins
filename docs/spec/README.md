# Singer spec concepts

This page summarizes the main concepts of the [Singer Specification](https://hub.meltano.com/singer/spec/). For the full spec and message details, see the official Singer Spec documentation.

## Messages

Singer defines three JSON-formatted message types that flow between taps (extractors) and targets (loaders):

| Message | Purpose |
|--------|--------|
| **SCHEMA** | Describes the structure of a stream’s data (JSON Schema) and key properties. Emitted once per stream before any RECORD messages. |
| **RECORD** | Carries the actual row/entity data for a stream. Each message includes a `stream` name and a `record` payload. |
| **STATE** | Tracks progress (e.g. bookmarks) so the next run can resume. Optional; format is tap-defined. |

Taps output these messages to **stdout**; targets read them from **stdin**. See the [Singer Spec — Messages](https://hub.meltano.com/singer/spec/) section for required/optional fields and examples.

## Taps vs targets

- **Taps** (extractors) read from a **source** (API, database, file) and write **SCHEMA**, **RECORD**, and **STATE** messages to stdout.
- **Targets** (loaders) read those messages from stdin and write data to a **destination** (database, warehouse, file).

Pipelines compose them with a Unix pipe: `tap-source | target-destination`. The [Singer Spec](https://hub.meltano.com/singer/spec/) describes taps and targets in more detail.

## Config file, state file, and Catalog

| File | Used by | Purpose |
|------|--------|---------|
| **Config file** | Tap (required), target (optional) | Credentials, endpoints, and other run parameters (e.g. `start_date`, `user_agent`). |
| **State file** | Tap (optional) | Input state from the last run; tap uses it to resume (e.g. incremental bookmarks). |
| **Catalog** | Tap (optional) | Which streams and properties to extract; produced by **Discovery** (`--discover`) and can be edited for selection. |

Discovery mode (`tap --config config.json --discover`) outputs the Catalog to stdout so it can be saved to a catalog file (e.g. `catalog.json`). For implementation details (e.g. how the SDK handles these), see [SDK Implementation](https://sdk.meltano.com/en/latest/implementation/index.html).
