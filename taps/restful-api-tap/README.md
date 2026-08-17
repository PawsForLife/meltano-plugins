# restful-api-tap
![singer_rest_api_tap](https://user-images.githubusercontent.com/84364906/220881634-c0d0145a-ab85-44e9-91b6-e8d365da25f3.png)

`restful-api-tap` is a Singer tap for generic REST APIs (Python package `restful_api_tap`). It supports schema auto-discovery, multiple authentication methods, and flexible pagination—including optional `pagination_stop_on_duplicate_token` for JSONPath pagination when APIs repeat the final cursor.

**Requirements:** Python 3.14+.

### Documentation

Full user documentation (installation, configuration, pagination, API examples, usage) lives in **[README/index.md](README/index.md)**:

| Topic | Document |
|-------|----------|
| Overview & auth summary | [README/overview.md](README/overview.md) |
| Meltano install & settings list | [README/installation.md](README/installation.md) |
| Config reference | [README/configuration.md](README/configuration.md) |
| Pagination | [README/pagination.md](README/pagination.md) |
| Example env exports | [README/examples.md](README/examples.md) |
| CLI usage & dev link | [README/usage.md](README/usage.md) |

### Install from this monorepo

Add to `meltano.yml`, then run `meltano install`. Use a plain `git+https://...` URL with `#subdirectory=taps/restful-api-tap` (see [repo root README](https://github.com/PawsForLife/meltano-plugins)).

```yaml
plugins:
  extractors:
    - name: restful-api-tap
      namespace: restful_api_tap
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap
```

For troubleshooting, target-gcs, and monorepo conventions, see the [repo root README](https://github.com/PawsForLife/meltano-plugins) and [docs/monorepo](../../docs/monorepo/README.md).
