# Changelog

<!--next-version-placeholder-->

## [Unreleased]

### Changed

- **README:** Clarified "Naming with chunking": added comma before "so" in chunk-index sentence; rewrote timestamp explanation so collisions are defined by chunk start time within the same granularity window (e.g. 12:00:00.500 vs 12:00:00.999), not by processing duration.

- **Glossary alignment:** Plugin, package, and directory were renamed for Singer/Meltano glossary alignment: CLI/plugin `target-gcs`, Python package `gcs_target`, path `loaders/target-gcs/`. See the [repo root CHANGELOG](../../CHANGELOG.md) for user migration (update `meltano.yml` to use `target-gcs`, re-run `meltano install`).

### Breaking

- **Credentials**: Remove `credentials_file` from config. Authentication uses Application Default Credentials (ADC) only. To use a credentials file, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable; the target no longer accepts a credentials path in config.

## v1.1.0 (2023-03-01)
### Feature
* Make gcp service account credential file optional ([`6e9e36e`](https://github.com/Datateer/target-gcs/commit/6e9e36ec3a9fee4d2e16b994ecade8ddd8eb61c1))

## v1.0.3 (2022-05-27)
### Fix
* Bump version ([`494d3c9`](https://github.com/Datateer/target-gcs/commit/494d3c90c1c58191a9023d95ebeb61995441fa49))

## v1.0.2 (2022-05-26)
### Fix
* Typo ([`b70e738`](https://github.com/Datateer/target-gcs/commit/b70e73870e472516bdf12c2ee592506c0df7a721))

## v1.0.1 (2022-05-26)
### Fix
* Semantic release ([`172004b`](https://github.com/Datateer/target-gcs/commit/172004b412baf115f5a50bf0c391eaf2a16b1484))
