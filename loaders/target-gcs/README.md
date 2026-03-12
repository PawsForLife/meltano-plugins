# target-gcs

`target-gcs` is a Singer **target** that loads data into the **destination** (Google Cloud Storage). The Python package is `target_gcs`. In Meltano, this target runs as a **loader**.

Build with the [Meltano Target SDK](https://sdk.meltano.com).

## Installation

**Use from a Meltano project (recommended):** This is a custom plugin (not on the Meltano Hub or PyPI). Add the loader to your project's `meltano.yml` with `pip_url` and `namespace: target_gcs`; do not set `variant`. Then run `meltano install`.

```yaml
plugins:
  loaders:
    - name: target-gcs
      namespace: target_gcs
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=loaders/target-gcs
```

See the [repo root README](../../README.md) for full instructions and troubleshooting.

**Local development:** From the repo root, clone and run:

```bash
cd loaders/target-gcs
./install.sh
```

Or install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run `uv sync --extra dev` in this directory.

## Supported formats

JSONL is the only supported output format

## Configuration

The target is configured via [Meltano](https://meltano.com/): settings and `config` are defined in `meltano.yml`, with optional overrides via environment variables (see table below). For an example structure, see `meltano.yml` in this directory.

### Accepted Config Options

| Property              | Env variable                         | Type    | Required | Default       | Description                                                                                                                                                                                                                                                                                      |
| --------------------- | ------------------------------------ | ------- | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| bucket_name           | TARGET_GCS_BUCKET_NAME               | string  | yes      | n/a           | The name of the GCS bucket                                                                                                                                                                                                                                                                       |
| date_format           | TARGET_GCS_DATE_FORMAT               | string  | no       | %Y-%m-%d      | If `{date}` token is used in key_naming_convention, the date will be formatted with this format string                                                                                                                                                                                           |
| key_prefix            | TARGET_GCS_KEY_PREFIX                | string  | no       | None          | A static prefix before the generated key names. If this and `key_naming_convention` are both provided, they will be combined.                                                                                                                                                                    |
| key_naming_convention | TARGET_GCS_KEY_NAMING_CONVENTION     | string  | no       | Conditional: when `partition_date_field` is set and omitted → `{stream}/{partition_date}/{timestamp}.jsonl`; when unset and omitted → `{stream}_{timestamp}.jsonl` | Template for object keys. When omitted: if `partition_date_field` is set, default is `{stream}/{partition_date}/{timestamp}.jsonl` (hive-style); if unset, default is `{stream}_{timestamp}.jsonl`. Tokens: `date`, `stream`, `timestamp`. When `partition_date_field` is set, `{partition_date}` and `{hive}` (alias for `{partition_date}`) are available. When chunking is enabled (`max_records_per_file` > 0), `{chunk_index}` (0-based) is also available and `{timestamp}` is recomputed at the start of each new chunk. Date format uses [python date format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). |
| max_records_per_file  | TARGET_GCS_MAX_RECORDS_PER_FILE      | integer | no       | 0             | When set and greater than 0, the target rotates to a new GCS object after that many records per stream; when 0 or omitted, one file per stream per run (unchanged).                                                                                                                              |
| partition_date_field  | TARGET_GCS_PARTITION_DATE_FIELD      | string  | no       | n/a           | Record property name used to build partition path (e.g. `created_at`, `updated_at`). When set, partition-by-field is enabled and the `{partition_date}` token is available in `key_naming_convention`.                                                                                           |
| partition_date_format | TARGET_GCS_PARTITION_DATE_FORMAT     | string  | no       | year=%Y/month=%m/day=%d | strftime-style format for the partition path segment (e.g. Hive-style `year=YYYY/month=MM/day=DD`). Used when resolving `{partition_date}` and for fallback when the record field is missing or unparseable.                                                                                    |

**File chunking (optional):** When `max_records_per_file` is set and greater than 0, the target writes multiple files per stream; each file contains at most that many records, and the last file for a stream may have fewer. When 0 or omitted, one file per stream per run is written (no chunking).

**Naming with chunking:** You can keep keys unique across chunks in two ways. (1) **Timestamp-based:** Use `{timestamp}` (and optionally `{date}`, `{stream}`). The timestamp is recomputed at the start of each new chunk, so keys differ unless consecutive chunks start within the same timestamp granularity window (e.g. two chunks starting at 12:00:00.500 and 12:00:00.999 get identical `{timestamp}` values). `{chunk_index}` is not required. (2) **Chunk-index-based:** Include `{chunk_index}` in the pattern, so each chunk has a distinct key regardless of timing—useful when many chunks can start within the same second, or when you want a fixed or run-level name with only the index varying.

See `meltano.yml` in this directory for an example `config` block; it may include `max_records_per_file` to demonstrate chunking.

### Hive partitioning by record date field

When you set `partition_date_field` to a record property name (e.g. `created_at`, `updated_at`), the target builds a partition path per record from that field and exposes it as the `{partition_date}` token in `key_naming_convention`. With partition-by-field enabled and no custom key template, object keys follow `{stream}/{partition_date}/{timestamp}.jsonl`. `{hive}` is an alias for `{partition_date}` in the key template when partition-by-field is on. Use `partition_date_format` (strftime-style) to control the path segment; the default is `year=%Y/month=%m/day=%d` (Hive-style, e.g. `year=2024/month=03/day=11`). The `{date}` token is unchanged: it always represents the run date (formatted with `date_format`), not the record’s partition date.

**Fallback:** If the record is missing the field or the value is unparseable (not a valid date/datetime string), the target uses the run date formatted with `partition_date_format` as the partition path and does not raise an error.

**Example:** To write keys like `{stream}/export_date=year=2024/month=03/day=11/{timestamp}.jsonl` using the record’s date field, set the loader `config` in `meltano.yml`:

```yaml
plugins:
  loaders:
    - name: target-gcs
      namespace: target_gcs
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=loaders/target-gcs
      config:
        bucket_name: my-bucket
        partition_date_field: created_at
        partition_date_format: "year=%Y/month=%m/day=%d"
        key_naming_convention: "{stream}/export_date={partition_date}/{timestamp}.jsonl"
```

**Chunking:** When both `max_records_per_file` and `partition_date_field` are set, the target rotates to a new file after that many records **within the current partition**. The partition path stays the same; the new file uses a new timestamp (and optionally `{chunk_index}`) in the key.

A full list of supported settings and capabilities for this
target is available by running:

```bash
target-gcs --about
```

### Authentication

Authentication uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials). No credentials path is accepted in the target config file. To use a service account key file, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the JSON key file; the target always uses the default client and does not read a credentials path from the config file.

### Configure using environment variables

Configuration is recommended via Meltano (`meltano.yml`) or environment variables rather than JSON config files. This Singer target will automatically import any environment variables within the working directory's `.env` if `--config=ENV` is provided, so that config can be supplemented or overridden by matching environment variables set in the terminal context or in the `.env` file.

### Source Authentication and Authorization

This target writes to GCS only; it does not require source-specific authentication. GCS access uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) or `GOOGLE_APPLICATION_CREDENTIALS` as described in the Authentication section above.

## Usage

You can easily run `target-gcs` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

```bash
target-gcs --version
target-gcs --help
# With Meltano (config from meltano.yml; recommended):
meltano run tap-carbon-intensity target-gcs
```

For non-Meltano use, supply config via environment variables: `tap-carbon-intensity | target-gcs --config=ENV` (with `TARGET_GCS_*` vars or a `.env` file in the working directory).

## Developer Resources

Requires **Python 3.12+**. The project uses **uv** for dependency management and **Ruff** and **mypy** for linting, formatting, and type checking. The lockfile is `uv.lock`.

### Initialize your Development Environment

**Option A (recommended):** Run the install script to ensure uv is available, create a clean virtual environment, install dependencies (including dev), and run pytest, ruff, and mypy:

```bash
./install.sh
```

**Option B:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then:

```bash
uv sync --extra dev
```

### Lint, format, and type check

```bash
uv run ruff check .
uv run ruff format .          # format in place; CI runs ruff format --check
uv run mypy target_gcs
```

### Create and Run Tests

Create tests in the package-root `tests/` directory and run:

```bash
uv run pytest
```

You can also run the `target-gcs` CLI directly:

```bash
uv run target-gcs --help
```

### Testing with [Meltano](https://meltano.com/)

_**Note:** This target will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install Meltano with uv (if needed)
uv tool install meltano
# From this directory, install plugins
cd loaders/target-gcs
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke target-gcs --version
# OR run a test `elt` pipeline with the Carbon Intensity sample tap:
meltano elt tap-carbon-intensity target-gcs
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the Meltano SDK to
develop your own Singer taps and targets.
