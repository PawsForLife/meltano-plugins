# New systems — Singer SDK docs

## New assets

All new assets are documentation under `docs/`.

### Directory structure

```
docs/
├── README.md          # Index / entry point; links to subdirs and external SDK/Spec
├── spec/              # Singer spec concepts (messages, taps, targets, files)
│   └── README.md
├── taps/              # Building taps with the SDK
│   └── README.md
├── targets/           # Building targets with the SDK
│   └── README.md
├── monorepo/          # Using plugins from this repo (pip_url, subdirectory)
│   └── README.md
└── (optional) testing.md or taps/testing.md  # SDK testing; only if not folded into taps/README
```

### Document list

| Path | Purpose |
|------|---------|
| `docs/README.md` | Docs index: overview, TOC to spec/taps/targets/monorepo, and links to [Meltano Singer SDK](https://sdk.meltano.com/en/latest/) and [Singer Spec](https://hub.meltano.com/singer/spec/). |
| `docs/spec/README.md` | Singer spec: message types (schema, record, state), taps vs targets, config/state/catalog files. Links to Singer Spec and SDK where relevant. |
| `docs/taps/README.md` | How to create taps: Tap/Stream classes, cookiecutter, REST/GraphQL/SQL, config schema. Links to SDK Getting Started, guides, and class reference. |
| `docs/targets/README.md` | How to create targets: Target/Sink classes, RecordSink vs BatchSink. Links to SDK Getting Started, sinks guide, and class reference. |
| `docs/monorepo/README.md` | Importing plugins from this repo: `pip_url` with `#subdirectory=taps/...` or `loaders/...`, directory layout; points to repo README. |

### Constraints

- Each doc file ≤500 lines (per content_length rule).
- No new code, tests, or config files.
