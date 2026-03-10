# Singer SDK documentation

This folder contains documentation for creating [Meltano](https://meltano.com/) plugins with the [Meltano Singer SDK](https://sdk.meltano.com/en/latest/) and understanding the [Singer Spec](https://hub.meltano.com/singer/spec/). It also explains how to use custom plugins from this repo (not on the Meltano Hub) in a Meltano project.

## Contents

| Section | Description |
|--------|-------------|
| [Singer spec](spec/) | Singer message types (SCHEMA, RECORD, STATE), taps vs targets, and config file, state file, Catalog. |
| [Building taps](taps/) | How to build extractors (taps) with the Singer SDK. |
| [Building targets](targets/) | How to build loaders (targets) with the Singer SDK. |
| [Using this monorepo](monorepo/) | Installing and using custom plugins from this repo (add via `meltano.yml` and `pip_url`; see [monorepo](monorepo/) for steps). |

## External references

- **[Meltano Singer SDK](https://sdk.meltano.com/en/latest/)** — Official SDK documentation (Getting Started, guides, class reference, testing).
- **[Singer Spec](https://hub.meltano.com/singer/spec/)** — The open standard for data exchange used by taps and targets.
