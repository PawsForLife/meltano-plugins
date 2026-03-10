# Building taps with the Singer SDK

This page explains how to build **taps** (extractors) using the [Meltano Singer SDK](https://sdk.meltano.com/en/latest/). Taps read from a **source** and emit Singer **SCHEMA**, **RECORD**, and **STATE** messages to stdout.

## Goal

Implement a tap by defining a **Tap** class and one or more **stream** classes. The SDK handles Singer protocol, discovery, and sync; you focus on configuration, stream definition, and how to fetch data.

## Getting started

1. **Scaffold a project** with the SDK cookiecutter:

   ```bash
   cookiecutter https://github.com/meltano/sdk --directory="cookiecutter/tap-template"
   cd tap-myapi   # or your tap name
   uv sync
   ```

2. **Implement your Tap** (configuration and stream discovery) and at least one **stream** class. For REST APIs, subclass `RESTStream` and set `name`, `path`, `primary_keys`, and `schema` (or `records_jsonpath` if the API wraps records in a key). See [SDK Getting Started](https://sdk.meltano.com/en/latest/dev_guide.html) for the full walkthrough.

3. **Run discovery** to emit the catalog: `tap-myapi --config config.json --discover`

4. **Run sync** (with optional state file and catalog): `tap-myapi --config config.json [--state state.json] [--catalog catalog.json]`

## Stream types

Choose the stream base class that matches your source:

| Type | Base class | Use when |
|------|------------|----------|
| **REST** | `RESTStream` | Data comes from REST APIs (JSON). |
| **GraphQL** | `GraphQLStream` | Data comes from a GraphQL API (inherits from REST). |
| **SQL** | `SQLStream` | Data comes from a SQL database (use with `SQLTap`). |
| **Generic** | `Stream` | Custom or non-REST extraction. |

See the [SDK Reference — Stream classes](https://sdk.meltano.com/en/latest/reference.html) (e.g. `Stream`, `RESTStream`, `GraphQLStream`, `SQLStream`) for details.

## Config

Define a JSON Schema for tap configuration via `config_jsonschema` on your Tap class. Common properties include API URL, credentials, `start_date`, and `user_agent`. The SDK validates config at startup. See [Defining a configuration schema](https://sdk.meltano.com/en/latest/guides/config-schema.html) and the [Getting Started](https://sdk.meltano.com/en/latest/dev_guide.html) guide.

## Testing

Use the SDK’s test helpers to run discovery and sync against fixtures or mocks. See [Testing Taps & Targets](https://sdk.meltano.com/en/latest/testing.html) for the testing framework and examples.

## Further reading

- [In-depth Guides](https://sdk.meltano.com/en/latest/guides/index.html) — Porting, pagination, schema sources, SQL taps, etc.
- [SDK Code Samples](https://sdk.meltano.com/en/latest/code_samples.html) — Copy-paste examples for common scenarios.
