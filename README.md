# meltano-plugins

Monorepo of [Meltano](https://meltano.com/) / [Singer SDK](https://sdk.meltano.com/) plugins (Meltano extractors and loaders—Singer taps and targets) maintained by PawsForLife. All plugins in this repo are forks of upstream projects that we modify for our use; sources are listed below.

**Repository:** [github.com/PawsForLife/meltano-plugins](https://github.com/PawsForLife/meltano-plugins) (public)

---

## Plugins

| Plugin | Type | Description | Upstream source |
|--------|------|-------------|-----------------|
| **restful-api-tap** | Extractor (tap) | Singer tap that extracts from REST API sources; auto-discovered stream schemas. Supports multiple auth types (Basic, API Key, Bearer, OAuth, AWS). | [Widen/tap-rest-api-msdk](https://github.com/Widen/tap-rest-api-msdk) |
| **target-gcs** | Loader (target) | Singer target that loads data to Google Cloud Storage (destination). Writes JSONL to a configurable bucket with configurable key naming. | [Datateer/target-gcs](https://github.com/Datateer/target-gcs) |

Both are heavily modified from their upstreams; we use plugin names `restful-api-tap` and `target-gcs` for Meltano.

---

## Installation

These plugins are **custom** (not published to the Meltano Hub or PyPI). Add them to your Meltano project by editing `meltano.yml` with `pip_url` pointing at this repo and, if you like, `variant: petcircle`. Do not add them via `meltano add` from the Hub.

Install from this GitHub repo using Meltano’s `pip_url` and the **subdirectory** fragment so each plugin is installed from its own path.

### 1. Add the plugin in `meltano.yml`

Use the `#subdirectory=` fragment in `pip_url` so Meltano installs the correct package from this monorepo.

**Extractor (restful-api-tap):**

```yaml
plugins:
  extractors:
    - name: restful-api-tap
      variant: petcircle
      pip_url: "restful-api-tap @ git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap"
      # Optional: pin to a ref (branch, tag, or commit)
      # pip_url: "restful-api-tap @ git+https://github.com/PawsForLife/meltano-plugins.git@v1.0.0#subdirectory=taps/restful-api-tap"
```

**Loader (target-gcs):**

```yaml
plugins:
  loaders:
    - name: target-gcs
      variant: petcircle
      pip_url: "target-gcs @ git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=loaders/target-gcs"
```

### 2. Install and run

```bash
meltano install
```

Then run your pipelines as usual (e.g. `meltano run restful-api-tap target-gcs`).

### Version pinning

To pin to a tag, branch, or commit, put the ref before `#`:

```yaml
pip_url: "restful-api-tap @ git+https://github.com/PawsForLife/meltano-plugins.git@v1.0.0#subdirectory=taps/restful-api-tap"
```

---

## Directory layout

- `taps/restful-api-tap/` — **restful-api-tap** (Singer tap for REST API sources; Meltano extractor (tap))
- `loaders/target-gcs/` — **target-gcs** (Singer target for GCS; Meltano loader (target))

Each subdirectory is a standalone Python package with its own `pyproject.toml` and is installable via `pip` from that path.

---

## Documentation

See [docs/](docs/README.md) for guides on creating Meltano plugins with the Singer SDK, the Singer spec, and using plugins from this monorepo.

---

## References

- [Meltano — Plugin management (custom fork)](https://docs.meltano.com/guide/plugin-management/#using-a-custom-fork-of-a-plugin)
- [Meltano — Plugin definition syntax](https://docs.meltano.com/reference/plugin-definition-syntax/) — `name`, `variant`, `pip_url`
- [pip VCS support](https://pip.pypa.io/en/stable/topics/vcs-support/) — `subdirectory` and URL fragments
