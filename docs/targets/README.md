# Building targets with the Singer SDK

This page explains how to build **targets** (loaders) using the [Meltano Singer SDK](https://sdk.meltano.com/en/latest/). Targets read Singer **SCHEMA**, **RECORD**, and **STATE** messages from stdin and write data to a **destination**.

## Goal

Implement a target by defining a **Target** class and a **Sink** class. The SDK handles Singer protocol and routing; you focus on configuration and how to write records (per record or in batches).

## Getting started

1. **Scaffold a project** with the SDK cookiecutter:

   ```bash
   cookiecutter https://github.com/meltano/sdk --directory="cookiecutter/target-template"
   cd target-mydb   # or your target name
   uv sync
   ```

2. **Implement your Target** (configuration, `default_sink_class`) and a **Sink** that processes records. See [SDK Getting Started](https://sdk.meltano.com/en/latest/dev_guide.html) for the full walkthrough.

3. **Run** the target: `tap-source --config tap.json | target-mydb --config target.json`

## Sink types

Choose how your target writes data:

| Type | Base class | Use when |
|------|------------|----------|
| **Record** | `RecordSink` | Write one record at a time via `process_record(record, context)`. |
| **Batch** | `BatchSink` | Accumulate records and write in batches via `start_batch()`, `process_record()`, and `process_batch()`. |

See [How to design a Sink](https://sdk.meltano.com/en/latest/sinks.html) and the [SDK Reference — Sink classes](https://sdk.meltano.com/en/latest/reference.html) for details.

## Config

Define a JSON Schema for target configuration via `config_jsonschema` on your Target class (e.g. host, port, database, credentials). The SDK validates config at startup. See [Defining a configuration schema](https://sdk.meltano.com/en/latest/guides/config-schema.html) and the [Getting Started](https://sdk.meltano.com/en/latest/dev_guide.html) guide.

## Testing

Use the SDK’s test helpers to run the target against fixtures or mocks. See [Testing Taps & Targets](https://sdk.meltano.com/en/latest/testing.html) for the testing framework and examples.

## Further reading

- [In-depth Guides](https://sdk.meltano.com/en/latest/guides/index.html) — Performance, SQL targets, etc.
- [SDK Code Samples](https://sdk.meltano.com/en/latest/code_samples.html) — Copy-paste examples for common scenarios.
