# Meltano & Singer Terminology Glossary

This document is the project’s **source of truth** for Meltano and Singer terminology. Use it to align documentation, file names, and code with official Meltano/Singer definitions. Definitions are derived from the [Meltano Singer SDK](https://sdk.meltano.com/en/latest/) and the [Singer Spec](https://hub.meltano.com/singer/spec); terms are not invented—only those that appear or are clearly implied in that documentation are included.

---

## Core concepts

### ELT

**Extract, Load, Transform.** A data pipeline pattern where data is first extracted from sources, loaded into a destination (e.g. data warehouse), then transformed there. Meltano and Singer implement the extract and load steps; transformation is typically done by tools such as dbt. Pipelines are often expressed as `tap-source | target-destination`.

*Ref:* [SDK intro](https://sdk.meltano.com/en/latest/), [Singer Spec](https://hub.meltano.com/singer/spec)

### Pipeline

A data flow from a source to a destination. In Singer/Meltano, a pipeline is typically one tap (extractor) piping JSON messages to one target (loader), e.g. `tap-source | target-destination`. State and catalog files allow incremental runs to resume.

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [Meltano Replicate Data](https://docs.meltano.com/guide/integration#replication-methods)

### Singer Spec

The open standard that defines the format of data exchange between taps and targets. It specifies message types (SCHEMA, RECORD, STATE), catalog structure, and how taps and targets communicate via stdout/stdin. The Meltano Singer SDK builds connectors that are automatically compliant with this spec.

*Ref:* [Singer Spec](https://hub.meltano.com/singer/spec), [SDK](https://sdk.meltano.com/en/latest/)

---

## Taps and targets

### Tap

A **data extractor**: a program that reads data from a source (API, database, or file) and writes Singer-formatted messages (SCHEMA, RECORD, STATE) to standard output. Taps accept config (required), and optionally state and catalog. In Meltano, taps are run as **extractors**. Naming convention: `tap-<source>` (e.g. `tap-gitlab`).

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [Singer Spec – Taps](https://hub.meltano.com/singer/spec#taps)

### Target

A **data loader**: a program that reads Singer messages from standard input and loads data into a destination (database, warehouse, file, etc.). Targets may accept an optional config file. In Meltano, targets are run as **loaders**. Naming convention: `target-<destination>` (e.g. `target-snowflake`).

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [Singer Spec – Targets](https://hub.meltano.com/singer/spec#targets)

### Connector

A component that moves data to or from a system. In Singer/Meltano usage, “connector” often refers to a tap or target implementation (e.g. “600+ existing connectors” on Meltano Hub). The SDK uses “connector” for SQL database access: `SQLConnector` is the base for SQLAlchemy-based taps/targets.

*Ref:* [SDK Reference – SQLConnector](https://sdk.meltano.com/en/latest/reference.html)

### Plugin

In Meltano, a pluggable component (extractor, loader, transformer, utility, etc.). Singer taps and targets are implemented as Meltano **extractor** and **loader** plugins. “Plugin” is the Meltano term; “tap” and “target” are the Singer/spec terms for the extract and load components.

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [Meltano integration guide](https://docs.meltano.com/guide/integration#replication-methods)

---

## Streams and sinks

### Stream

(1) **In the Singer Spec:** A named set of data. Each RECORD and SCHEMA message includes a `stream` identifier (e.g. endpoint name for APIs, table name for databases). A stream corresponds to one logical entity (e.g. “users”, “orders”).
(2) **In the SDK:** The `Stream` class is the abstract base for tap streams; subclasses (e.g. `RESTStream`, `SQLStream`) define how data for that stream is fetched and emitted.

*Ref:* [Singer Spec – Messages](https://hub.meltano.com/singer/spec#messages), [SDK Reference – Stream](https://sdk.meltano.com/en/latest/classes/singer_sdk.Stream.html)

### Sink

In the SDK, the component of a **target** that receives and processes records. One sink typically handles one stream (1:1), but targets can implement 1:many (one stream to multiple sinks) or many:1 (all streams to one sink). Abstract base: `Sink`; common implementations: `RecordSink` (one record at a time), `BatchSink` (batches of records).

*Ref:* [SDK – Sinks](https://sdk.meltano.com/en/latest/sinks.html), [SDK Reference – Sink](https://sdk.meltano.com/en/latest/reference.html)

### RecordSink

SDK base class for targets that process **one record at a time**, via `process_record(record, context)`. Use when the destination API or storage expects record-by-record writes.

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [SDK Reference – RecordSink](https://sdk.meltano.com/en/latest/classes/singer_sdk.RecordSink.html)

### BatchSink

SDK base class for targets that process records **in batches**. Key methods: `start_batch()`, `process_record()` (to enqueue), `process_batch()` (to write the batch and clean up). Use when the destination supports bulk writes (e.g. database inserts, file writes).

*Ref:* [SDK Getting Started](https://sdk.meltano.com/en/latest/dev_guide.html), [SDK Reference – BatchSink](https://sdk.meltano.com/en/latest/classes/singer_sdk.BatchSink.html)

### RESTStream

SDK abstract base class for streams that extract data from **REST APIs**. Handles requests, pagination, and parsing of JSON responses (e.g. via `records_jsonpath`). Subclass to define `url_base`, `path`, `primary_keys`, schema, and optional authentication.

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [SDK Reference – RESTStream](https://sdk.meltano.com/en/latest/classes/singer_sdk.RESTStream.html)

### GraphQLStream

SDK base class for streams that extract from **GraphQL APIs**. Inherits from `RESTStream` (GraphQL is typically over HTTP).

*Ref:* [SDK Reference](https://sdk.meltano.com/en/latest/reference.html)

### SQLStream

SDK base class for streams that extract from **SQL databases** via SQLAlchemy. Used with `SQLTap`.

*Ref:* [SDK Reference](https://sdk.meltano.com/en/latest/reference.html)

---

## Messages and data structures

### Schema (message type)

A **SCHEMA** message defines the structure of the data for a stream. It includes: `stream` (identifier), `schema` (JSON Schema for the record payload), `key_properties` (primary key), and optionally `bookmark_properties`. Every stream must emit a SCHEMA message before any RECORD messages for that stream.

*Ref:* [Singer Spec – Schemas](https://hub.meltano.com/singer/spec#schemas)

### Record (message type)

A **RECORD** message carries one unit of extracted data. Required fields: `type: "RECORD"`, `stream`, `record` (JSON object). Optional: `time_extracted` (RFC3339). Records must be preceded by a SCHEMA message for the same stream.

*Ref:* [Singer Spec – Records](https://hub.meltano.com/singer/spec#records)

### State (message type)

A **STATE** message carries progress information the tap wants to persist (e.g. bookmarks for incremental sync). Required: `type: "STATE"`, `value` (JSON object). The structure of `value` is not fixed by the spec; the SDK and Singer community recommend a `bookmarks` object keyed by stream. Targets may emit state to stdout when committing data.

*Ref:* [Singer Spec – State](https://hub.meltano.com/singer/spec#state), [SDK – Stream State](https://sdk.meltano.com/en/latest/implementation/state.html)

### Catalog

A JSON structure that describes which streams (and optionally which properties) to extract and how they are replicated. It has a top-level `streams` array; each entry includes `stream`, `tap_stream_id`, `schema`, and optional `metadata`. Taps can **discover** (generate) a catalog with `--discover`; in sync mode they are typically given a catalog (e.g. from Meltano or a saved file).

*Ref:* [Singer Spec – Catalog Files](https://hub.meltano.com/singer/spec#catalog-files), [SDK – Discovery](https://sdk.meltano.com/en/latest/implementation/discovery.html)

### Discovery (discovery mode)

The process of generating a catalog. When a tap is run with `--discover`, it outputs the full list of available streams (and their schemas) to stdout. That output can be saved as a catalog file or used by Meltano to apply selection/metadata rules.

*Ref:* [Singer Spec – Discovery Mode](https://hub.meltano.com/singer/spec#discovery-mode), [SDK – Catalog Discovery](https://sdk.meltano.com/en/latest/implementation/discovery.html)

### Config (config file)

A JSON file (e.g. `config.json`) that supplies parameters needed for the tap or target to run (credentials, API URLs, start date, etc.). Taps require a config file; targets may use one if the destination needs configuration.

*Ref:* [Singer Spec – Config Files](https://hub.meltano.com/singer/spec#config-files)

### State file

A JSON file (e.g. `state.json`) that stores state between runs. Its structure typically matches the `value` of STATE messages (e.g. `bookmarks` per stream). Passed to taps so they can resume from the last bookmark; the tap may output updated state as STATE messages.

*Ref:* [Singer Spec – State Files](https://hub.meltano.com/singer/spec#state-files), [SDK – Stream State](https://sdk.meltano.com/en/latest/implementation/state.html)

---

## Replication and state

### Replication method

How a stream is synced. Common values in catalog metadata: **FULL_TABLE** (full refresh each run), **INCREMENTAL** (only new/changed data using a replication key), **LOG_BASED** (change data capture from transaction logs). Set via catalog metadata (e.g. `replication-method`).

*Ref:* [Singer Spec – Metadata](https://hub.meltano.com/singer/spec#metadata), [Meltano – Replication methods](https://docs.meltano.com/guide/integration#replication-methods)

### FULL_TABLE

Replication method that extracts the entire dataset for the stream on each sync (no bookmarks).

*Ref:* [Singer Spec – Metadata](https://hub.meltano.com/singer/spec), [Meltano integration](https://docs.meltano.com/guide/integration#replication-methods)

### INCREMENTAL

Replication method that only extracts records that are new or updated since the last run, using a **replication key** (e.g. `updated_at`) and stored **state** (bookmarks).

*Ref:* [Singer Spec – Metadata](https://hub.meltano.com/singer/spec), [SDK – State](https://sdk.meltano.com/en/latest/implementation/state.html)

### LOG_BASED

Replication method that uses the source system’s transaction or change log (e.g. database binlog) to stream changes. Requires tap support (e.g. `TapCapabilities.LOG_BASED`).

*Ref:* [Singer Spec – Metadata](https://hub.meltano.com/singer/spec), [SDK Capabilities](https://sdk.meltano.com/en/latest/capabilities.html)

### Incremental replication

Syncing only new or changed data using a replication key and persisted state (bookmarks), as opposed to full table refresh.

*Ref:* [SDK](https://sdk.meltano.com/en/latest/), [SDK State](https://sdk.meltano.com/en/latest/implementation/state.html)

### Replication key

A property (e.g. `updated_at`, `id`) used to determine which records to extract in **INCREMENTAL** replication. The tap stores the last seen value in state (bookmarks) and uses it on the next run. Declared in schema `bookmark_properties` and in catalog metadata (e.g. `replication-key`). The SDK uses a single replication key per stream (multiple keys are handled via partitioning where applicable).

*Ref:* [Singer Spec – State, Metadata](https://hub.meltano.com/singer/spec), [SDK State](https://sdk.meltano.com/en/latest/implementation/state.html)

### Bookmark

Stored value(s) that indicate how far a stream has been synced (e.g. last `updated_at` or last `id`). Stored in state under `bookmarks.<stream_name>`. Used to resume incremental sync on the next run.

*Ref:* [Singer Spec – State](https://hub.meltano.com/singer/spec#state), [SDK State](https://sdk.meltano.com/en/latest/implementation/state.html)

### State (stream state / bookmarks)

The persisted progress of extraction per stream. In the SDK, state is typically keyed by stream and holds at least `replication_key` and `replication_key_value`. The Singer spec does not mandate a format; the SDK and docs recommend a `bookmarks` object. Targets may write state to stdout when they commit data (e.g. after draining a sink).

*Ref:* [SDK – Stream State](https://sdk.meltano.com/en/latest/implementation/state.html), [Singer Spec – State](https://hub.meltano.com/singer/spec#state)

---

## Stream maps and transformation

### Stream map

A configuration that transforms or routes streams and their records between tap and target. Supports aliasing, filtering, property renames, property add/remove, and schema flattening. Configured via `stream_maps` (and optionally `stream_map_config`). SDK taps and targets apply stream maps automatically; the standalone **meltano-map-transformer** can apply them between any Singer tap and target.

*Ref:* [SDK – Inline Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html)

### stream_maps

Config key (object) mapping stream names to transformation rules. Each rule can alias, drop, or add properties using expressions (e.g. `email: __NULL__`, `email_domain: owner_email.split('@')[-1]`). Used by taps (before output) and targets (before sink processing).

*Ref:* [SDK – Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html)

### stream_map_config

Optional config passed into stream map expressions (e.g. a `config` dict available in expressions). Used for things like a hash seed or other parameters needed by the mapping logic.

*Ref:* [SDK – Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html)

### Inline mapper

A component that applies stream maps. Can be the tap or target (when built with the SDK) or the standalone **meltano-map-transformer** plugin. Mappers do not perform aggregation, joins, or external API lookups; they only transform or route stream/record data.

*Ref:* [SDK – Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html), [SDK Reference – InlineMapper](https://sdk.meltano.com/en/latest/reference.html)

---

## Batch and extensions

### BATCH (message type)

An extension to the Singer protocol that sends records in bulk via files rather than one RECORD per line. The message includes `stream`, `encoding` (e.g. format and compression), and `manifest` (list of file URIs). Batch files contain raw records (e.g. JSONL), not Singer RECORD messages. Supports backpressure and bulk exports (e.g. DB dumps). Preview in the SDK; local filesystem and S3 are supported.

*Ref:* [SDK – Batch Messages](https://sdk.meltano.com/en/latest/batch.html)

### ACTIVATE_VERSION

A Singer protocol extension used to signal a full replacement of a stream’s data (e.g. for hard deletes or version resets). Targets that support hard deletes may require a tap that emits ACTIVATE_VERSION. Tied to capabilities `activate-version`, `hard-delete`, and `soft-delete`.

*Ref:* [SDK Capabilities](https://sdk.meltano.com/en/latest/capabilities.html), [Singer Spec / Hub](https://hub.meltano.com/singer/docs#activate-version)

---

## SDK and implementation terms

### Key properties

The primary key of a stream: list of property names that uniquely identify a record (e.g. `["id"]`). Appears in SCHEMA messages as `key_properties` and in catalog metadata (e.g. `table-key-properties`). In the SDK, set on streams via `primary_keys`.

*Ref:* [Singer Spec – Schemas](https://hub.meltano.com/singer/spec#schemas), [SDK Discovery](https://sdk.meltano.com/en/latest/implementation/discovery.html)

### Primary keys

In the SDK, the stream attribute that defines the primary key (list of strings). Used during discovery to populate the catalog and SCHEMA messages.

*Ref:* [SDK Discovery](https://sdk.meltano.com/en/latest/implementation/discovery.html)

### Metadata (catalog metadata)

Extra information attached to streams or properties in the catalog. Two kinds: **discoverable** (written and read by the tap, e.g. `inclusion`, `valid-replication-keys`) and **non-discoverable** (e.g. written by Meltano: `selected`, `replication-method`, `replication-key`). Each metadata entry has a `breadcrumb` (stream or property path) and a `metadata` object.

*Ref:* [Singer Spec – Metadata](https://hub.meltano.com/singer/spec#metadata)

### JSON Schema

The standard used in Singer to describe the structure and types of the `record` payload. Schema messages carry a JSON Schema; targets use it to create tables or validate data. The SDK provides typing helpers (e.g. `singer_sdk.typing`) to build these schemas.

*Ref:* [Singer Spec – Schemas](https://hub.meltano.com/singer/spec#schemas)

### Sink drain

When a target closes and flushes a sink (e.g. on a new STATE message for an already-active stream), it “drains” that sink: processes any queued records, then marks the sink as finished. State is written to stdout when sinks drain and when the sync completes.

*Ref:* [SDK – Sinks](https://sdk.meltano.com/en/latest/sinks.html), [SDK – Target State Output](https://sdk.meltano.com/en/latest/implementation/state.html#target-state-output)

### At least once

The Singer spec’s delivery guarantee: every source record will be processed by the target **at least once**. Duplicates are possible (e.g. due to retries or replication-key semantics); deduplication is typically done in the transformation layer (e.g. dbt).

*Ref:* [SDK – At Least Once](https://sdk.meltano.com/en/latest/implementation/at_least_once.html)

### Capabilities

Flags that declare what a tap or target supports (e.g. `discover`, `state`, `stream-maps`, `batch`, `activate-version`, `log-based`). Used by Meltano and the SDK to enable or validate features.

*Ref:* [SDK – Plugin Capabilities](https://sdk.meltano.com/en/latest/capabilities.html)

---

## Quick reference: message and file summary

| Term            | Meaning |
|-----------------|--------|
| **SCHEMA**      | Message defining stream structure (JSON Schema, key_properties, optional bookmark_properties). |
| **RECORD**      | Message carrying one data record for a stream. |
| **STATE**       | Message carrying persisted progress (e.g. bookmarks) for incremental sync. |
| **BATCH**       | Extension message pointing to files of bulk records (SDK preview). |
| **Catalog**     | JSON with `streams` (and optional metadata) describing what to extract and how. |
| **Config file** | JSON with credentials and parameters for tap/target. |
| **State file**  | JSON with bookmarks/state to resume incremental sync. |

---

*Glossary derived from [Meltano Singer SDK](https://sdk.meltano.com/en/latest/) and [Singer Spec](https://hub.meltano.com/singer/spec). Last aligned with SDK 0.53.5 docs.*
