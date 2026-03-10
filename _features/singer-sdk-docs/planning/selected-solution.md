# Selected solution — Singer SDK documentation

## Chosen structure

Documentation is added under `docs/` by topic. Each doc stays under 500 lines and links to the official Meltano Singer SDK and Singer Spec.

## Directory layout

```
docs/
├── README.md              # Index + external links
├── spec/
│   └── README.md          # Singer spec concepts
├── taps/
│   └── README.md          # Building taps
├── targets/
│   └── README.md          # Building targets
└── monorepo/
    └── README.md          # Using plugins from this repo
```

## Document outline for implementer

### 1. `docs/README.md`

- Short intro: purpose of this docs set (create Meltano plugins with Singer SDK; understand spec and repo).
- Bullet or table linking to: `spec/`, `taps/`, `targets/`, `monorepo/`.
- Primary external links:
  - [Meltano Singer SDK](https://sdk.meltano.com/en/latest/)
  - [Singer Spec](https://hub.meltano.com/singer/spec/)

### 2. `docs/spec/README.md`

- **Messages:** schema, record, state (what they are, one-line purpose). Link: [Singer Spec](https://hub.meltano.com/singer/spec/) (messages section).
- **Taps vs targets:** taps produce messages to stdout; targets consume from stdin; pipeline = tap | target. Link: Singer Spec "Taps" and "Targets."
- **Config / state / catalog:** brief description of config.json, state.json, catalog.json and discovery. Link: Singer Spec "Taps" (config, state, catalog), optional [SDK Implementation](https://sdk.meltano.com/en/latest/implementation/index.html).
- Keep to concepts; no SDK-specific API detail here.

### 3. `docs/taps/README.md`

- **Goal:** Build a tap with the Singer SDK.
- **Getting started:** Cookie cutter, `Tap` + stream class (e.g. `RESTStream`). Link: [SDK Getting Started (dev_guide)](https://sdk.meltano.com/en/latest/dev_guide.html).
- **Stream types:** REST, GraphQL, SQL; when to use which. Link: [SDK Reference — Stream classes](https://sdk.meltano.com/en/latest/reference.html) (Stream, RESTStream, GraphQLStream, SQLStream).
- **Config:** Config schema (e.g. `config_jsonschema`). Link: [Config schema guide](https://sdk.meltano.com/en/latest/guides/config-schema.html) if needed; dev_guide.
- **Testing:** Use SDK test framework; link: [SDK Testing](https://sdk.meltano.com/en/latest/testing.html). Optional: one subsection or short paragraph; if content grows, consider `docs/taps/testing.md` later.
- **Further:** Link to [In-depth Guides index](https://sdk.meltano.com/en/latest/guides/index.html), [SDK Code Samples](https://sdk.meltano.com/en/latest/code_samples.html).

### 4. `docs/targets/README.md`

- **Goal:** Build a target with the Singer SDK.
- **Getting started:** Cookie cutter, `Target` + `Sink`. Link: [SDK Getting Started (dev_guide)](https://sdk.meltano.com/en/latest/dev_guide.html).
- **Sink types:** RecordSink (per record) vs BatchSink (batches). Link: [How to design a Sink](https://sdk.meltano.com/en/latest/sinks.html), [SDK Reference — Sink classes](https://sdk.meltano.com/en/latest/reference.html).
- **Config:** Same idea as taps; link dev_guide / config guide.
- **Testing:** Link: [SDK Testing](https://sdk.meltano.com/en/latest/testing.html).
- **Further:** Link In-depth Guides, Code Samples.

### 5. `docs/monorepo/README.md`

- **Purpose:** Use plugins from this repo (meltano-plugins) in a Meltano project.
- **Mechanism:** `pip_url` with Git URL and `#subdirectory=` fragment. Example: `tap-rest-api-msdk` from `taps/restful-api-tap`, `target-gcs` from `loaders/gcs-loader`.
- **Concrete examples:** Copy or paraphrase the YAML snippets from the repo [README.md](../README.md) (Installation section): extractor and loader with `pip_url` and `#subdirectory=taps/restful-api-tap` / `#subdirectory=loaders/gcs-loader`.
- **Directory layout:** Point to repo README "Directory layout" (taps/restful-api-tap, loaders/gcs-loader; each is a standalone package with its own pyproject.toml).
- **Version pinning:** Ref before `#` (e.g. `@v1.0.0`). Link: [Meltano — Plugin management (custom fork)](https://docs.meltano.com/guide/plugin-management/#using-a-custom-fork-of-a-plugin), [Plugin definition syntax](https://docs.meltano.com/reference/plugin-definition-syntax/), [pip VCS support](https://pip.pypa.io/en/stable/topics/vcs-support/) (subdirectory).

## SDK and Singer URLs to use

| Topic | URL |
|-------|-----|
| SDK home | https://sdk.meltano.com/en/latest/ |
| SDK Getting Started | https://sdk.meltano.com/en/latest/dev_guide.html |
| SDK In-depth Guides | https://sdk.meltano.com/en/latest/guides/index.html |
| SDK Reference (classes) | https://sdk.meltano.com/en/latest/reference.html |
| SDK Testing | https://sdk.meltano.com/en/latest/testing.html |
| SDK Sinks | https://sdk.meltano.com/en/latest/sinks.html |
| Singer Spec | https://hub.meltano.com/singer/spec/ |

Monorepo doc: point to repo root README for Installation and Directory layout; no new mechanisms beyond what README already describes.
