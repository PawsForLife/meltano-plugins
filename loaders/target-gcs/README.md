# target-gcs

`target-gcs` is a Singer **target** that loads data into the **destination** (Google Cloud Storage). The Python package is `gcs_target`. In Meltano, this target runs as a **loader**.

Build with the [Meltano Target SDK](https://sdk.meltano.com).

## Installation

- [ ] `Developer TODO:` Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPi repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

```bash
pipx install target-gcs
```

## Supported formats

JSONL is the only supported output format

## Configuration

The target reads its settings from a **config file** (see `sample.config.json` for an example).

### Accepted Config Options

| Property              | Env variable                         | Type    | Required | Default       | Description                                                                                                                                                                                                                                                                                      |
| --------------------- | ------------------------------------ | ------- | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| bucket_name           | TARGET_GCS_BUCKET_NAME               | string  | yes      | n/a           | The name of the GCS bucket                                                                                                                                                                                                                                                                       |
| date_format           | TARGET_GCS_DATE_FORMAT               | string  | no       | %Y-%m-%d      | If `{date}` token is used in key_naming_convention, the date will be formatted with this format string                                                                                                                                                                                           |
| key_prefix            | TARGET_GCS_KEY_PREFIX                | string  | no       | None          | A static prefix before the generated key names. If this and `key_naming_convention` are both provided, they will be combined.                                                                                                                                                                    |
| key_naming_convention | TARGET_GCS_KEY_NAMING_CONVENTION     | string  | no       | `{timestamp}` | A prefix to add to the beginning of uploaded files. Tokens: `date`, `stream`, `timestamp`. When chunking is enabled (`max_records_per_file` > 0), `{chunk_index}` (0-based) is available and `{timestamp}` is refreshed at the start of each new chunk; include `{chunk_index}` to avoid collisions when multiple chunks are created in the same second. Date format uses [python date format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). |
| max_records_per_file  | TARGET_GCS_MAX_RECORDS_PER_FILE      | integer | no       | 0             | When set and greater than 0, the target rotates to a new GCS object after that many records per stream; when 0 or omitted, one file per stream per run (unchanged).                                                                                                                              |

**File chunking (optional):** When `max_records_per_file` is set and greater than 0, the target writes multiple files per stream; each file contains at most that many records, and the last file for a stream may have fewer. When 0 or omitted, one file per stream per run is written (no chunking).

See `sample.config.json` for an example; the sample may include `max_records_per_file` to demonstrate chunking.

A full list of supported settings and capabilities for this
target is available by running:

```bash
target-gcs --about
```

### Authentication

Authentication uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials). No credentials path is accepted in the target config file. To use a service account key file, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the JSON key file; the target always uses the default client and does not read a credentials path from the config file.

### Configure using environment variables

This Singer target will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, so that config file values can be supplemented or overridden by matching environment variables set in the terminal context or in the `.env` file.

### Source Authentication and Authorization

- [ ] `Developer TODO:` If your target requires special access on the source system, or any special authentication requirements, provide those here.

## Usage

You can easily run `target-gcs` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

```bash
target-gcs --version
target-gcs --help
# Test using the "Carbon Intensity" sample:
tap-carbon-intensity | target-gcs --config /path/to/target-gcs-config.json
```

## Developer Resources

The project uses **uv** for dependency management and **Ruff** and **mypy** for linting, formatting, and type checking. The lockfile is `uv.lock`.

### Initialize your Development Environment

**Option A (recommended):** Run the install script to ensure uv is available, create a clean virtual environment, install dependencies (including dev), and run pytest, ruff, and mypy:

```bash
./install.sh
```

**Option B:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then:

```bash
uv sync
```

### Lint, format, and type check

```bash
uv run ruff check .
uv run ruff format .          # format in place; CI runs ruff format --check
uv run mypy gcs_target
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
# Install meltano
pipx install meltano
# Initialize meltano within this directory
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
