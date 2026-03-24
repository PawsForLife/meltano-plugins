# Installation

[← Overview](overview.md) · [Documentation index](index.md) · [Configuration →](configuration.md)

### Install from this monorepo

This tap is a **custom** plugin (not on the Meltano Hub or PyPI). To use it from this repo, add the following to your project's `meltano.yml`, then run `meltano install`. Use `namespace` and omit `variant`; use a plain `git+https://...` URL (not the `package @ url` form—see [repo root README](https://github.com/PawsForLife/meltano-plugins)#troubleshooting).

```yaml
plugins:
  extractors:
    - name: restful-api-tap
      namespace: restful_api_tap
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap
```

For the full installation guide, troubleshooting, and the loader (target-gcs), see the [repo root README](https://github.com/PawsForLife/meltano-plugins) or [docs/monorepo](../../../docs/monorepo/README.md).

### Generic Meltano setup

If using via Meltano (e.g. from PyPI or another source), add the following lines to your `meltano.yml` file and run the following command:

```yaml
plugins:
  extractors:
    - name: restful-api-tap
      namespace: restful_api_tap
      pip_url: restful-api-tap
      executable: restful-api-tap
      capabilities:
        - state
        - catalog
        - discover
      settings:
        - name: api_url
          kind: string
        - name: next_page_token_path
          kind: string
        - name: pagination_stop_on_duplicate_token
          kind: boolean
        - name: pagination_request_style
          kind: string
        - name: pagination_response_style
          kind: string
        - name: use_request_body_not_params
          kind: boolean
        - name: backoff_type
          kind: string
        - name: backoff_param
          kind: string
        - name: backoff_time_extension
          kind: integer
        - name: store_raw_json_message
          kind: boolean
        - name: flatten_records
          kind: boolean
        - name: pagination_page_size
          kind: integer
        - name: pagination_results_limit
          kind: integer
        - name: pagination_next_page_param
          kind: string
        - name: pagination_limit_per_page_param
          kind: string
        - name: pagination_total_limit_param
          kind: string
        - name: pagination_initial_offset
          kind: integer
        - name: offset_records_jsonpath
          kind: string
        - name: streams
          kind: array
        - name: name
          kind: string
        - name: path
          kind: string
        - name: params
          kind: object
        - name: headers
          kind: object
        - name: records_path
          kind: string
        - name: primary_keys
          kind: array
        - name: replication_key
          kind: string
        - name: except_keys
          kind: array
        - name: num_inference_records
          kind: integer
        - name: start_date
          kind: date_iso8601
        - name: source_search_field
          kind: string
        - name: source_search_query
          kind: string
        - name: auth_method
          kind: string
        - name: api_key
          kind: object
        - name: client_id
          kind: password
        - name: client_secret
          kind: password
        - name: username
          kind: string
        - name: password
          kind: password
        - name: bearer_token
          kind: password
        - name: refresh_token
          kind: oauth
        - name: grant_type
          kind: string
        - name: scope
          kind: string
        - name: access_token_url
          kind: string
        - name: redirect_uri
          kind: string
        - name: oauth_extras
          kind: object
        - name: oauth_expiration_secs
          kind: integer
        - name: aws_credentials
          kind: object
```

```bash
meltano install extractor restful-api-tap
```

[← Overview](overview.md) · [Documentation index](index.md) · [Configuration →](configuration.md)
