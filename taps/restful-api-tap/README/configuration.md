# Configuration

[← Installation](installation.md) · [Documentation index](index.md) · [Pagination →](pagination.md)

### Accepted Config Options


A full list of supported settings and capabilities for this
tap is available by running:

```bash
restful-api-tap --about
```

#### Top-level config options.
Parameters that appear at the stream-level will overwrite their top-level
counterparts except where noted in the stream-level params. Otherwise, the values
provided at the top-level will be the default values for each stream.:
- `api_url`: required: the base url/endpoint for the desired api.
- `pagination_request_style`: optional: style for requesting pagination, defaults to `default` which is the `jsonpath_paginator`, see Pagination below.
- `pagination_response_style`: optional: style of pagination results, defaults to `default` which is the `page` style response, see Pagination below.
- `use_request_body_not_params`: optional: sends the request parameters in the request body. This is normally not required, a few API's like OpenSearch require this. Defaults to `False`.
- `backoff_type`: optional: The style of Backoff [message|header] applied to rate limited APIs. Backoff times (seconds) come from response either the `message` or `header`. Defaults to `None`.
- `backoff_param`: optional: the header parameter to inspect for a backoff time. Defaults to `Retry-After`.
- `backoff_time_extension`: optional: An additional extension (seconds) to the backoff time over and above a jitter value - use where an API is not precise in it's backoff times. Defaults to `0`.
- `store_raw_json_message`: optional: An additional extension which will emit the whole message into an field `_sdc_raw_json`. Useful for a dynamic schema which cannot be automatically discovered. Defaults to `False`.
- `flatten_records`: optional: When `true`, records and inferred schema are flattened (keys like `user_name` from nested `user.name`). When `false`, nested structure is preserved. Defaults to `false`. Stream-level value overrides top-level.
- `pagination_page_size`: optional: limit for size of page, defaults to None.
- `pagination_results_limit`: optional: limits the max number of records. Note: Will cause an exception if the limit is hit (except for the `restapi_header_link_paginator`). This should be used for development purposes to restrict the total number of records returned by the API. Defaults to None.
- `pagination_next_page_param`: optional: The name of the param that indicates the page/offset. Defaults to None.
- `pagination_limit_per_page_param`: optional: The name of the param that indicates the limit/per_page. Defaults to None.
- `pagination_total_limit_param`: optional: The name of the param that indicates the total limit e.g. total, count. Defaults to total
- `pagination_initial_offset`: optional: The initial offset for the first request. Defaults to 1.
- `offset_records_jsonpath`: optional: a jsonpath string representing the path to the records. Defaults to `None`.
- `next_page_token_path`: optional: a jsonpath string representing the path to the "next page" token. Defaults to `'$.next_page'` for the `jsonpath_paginator` paginator only otherwise None.
- `pagination_stop_on_duplicate_token`: optional: when `true`, JSONPath pagination stops if the next-page token equals the current token instead of raising a loop error (Singer SDK “loop detected in pagination”). Default `false`. Stream-level value overrides top-level. Applies when `pagination_request_style` is `jsonpath_paginator` or `default`. Use when the API repeats the last cursor on the final page while still returning HTTP 200—common for cursor/`after`-style APIs (e.g. Medallia sequence-id pagination). See [Pagination](pagination.md) (jsonpath_paginator).
- `streams`: required: a list of objects that contain the configuration of each stream. See stream-level params below.
- `path`: optional: see stream-level params below.
- `params`: optional: see stream-level params below.
- `headers`: optional: see stream-level params below.
- `records_path`: optional: see stream-level params below.
- `primary_keys`: optional: see stream-level params below.
- `replication_key`: optional: see stream-level params below.
- `except_keys`: optional: see stream-level params below.
- `num_inference_keys`: optional: see stream-level params below.
- `start_date`: optional: see stream-level params below.
- `source_search_field`: optional: see stream-level params below.
- `source_search_query`: optional: see stream-level params below.
- `auth_method`: optional: see authentication params below.
- `api_key`: optional: see authentication params below.
- `client_id`: optional: see authentication params below.
- `client_secret`: optional: see authentication params below.
- `username`: optional: see authentication params below.
- `password`: optional: see authentication params below.
- `bearer_token`: optional: see authentication params below.
- `refresh_token`: optional: see authentication params below.
- `grant_type`: optional: see authentication params below.
- `scope`: optional: see authentication params below.
- `access_token_url`: optional: see authentication params below.
- `redirect_uri`: optional: see authentication params below.
- `oauth_extras`: optional: see authentication params below.
- `oauth_expiration_secs`: optional: see authentication params below.
- `aws_credentials`: optional: see authentication params below.
- `offset_records_jsonpath`: optional: see pagination params below.

#### Stream level config options.
Parameters that appear at the stream-level
will overwrite their top-level counterparts except where noted below:
- `name`: required: name of the stream.
- `path`: optional: the path appended to the `api_url`.
- `params`: optional: an object of objects that provide the `params` in a `requests.get` method.
  Stream level params will be merged with top-level params with stream level params overwriting
  top-level params with the same key.
- `headers`: optional: an object of headers to pass into the api calls. Stream level
  headers will be merged with top-level params with stream level params overwriting
  top-level params with the same key
- `records_path`: optional: a jsonpath string representing the path in the requests response that contains the records to process. Defaults to `$[*]`.
- `flatten_records`: optional: When `true`, records and inferred schema are flattened; when `false`, nested structure is preserved. Defaults to `false`. Overrides top-level for this stream.
- `primary_keys`: required: a list of property names that form the stream’s key properties (primary keys in the SDK; appear as `key_properties` in SCHEMA messages).
- `replication_key`: optional: the json key of the replication key. Note that this should be an incrementing integer or datetime object.
- `except_keys`: This tap automatically flattens the entire json structure and builds keys based on the corresponding paths.
  Keys, whether composite or otherwise, listed in this dictionary will not be recursively flattened, but instead their values will be
  turned into a json string and processed in that format. This is also automatically done for any lists within the records; therefore,
  records are not duplicated for each item in lists.
- `num_inference_keys`: optional: number of records used to infer the stream's schema. Defaults to 50.
- `schema`: optional: A valid Singer schema or a path-like string that provides
  the path to a `.json` file that contains a valid Singer schema. If provided,
  the schema will not be inferred from the results of an api call.
- `start_date`: optional: used by the **offset**, **page**, and **hateoas_body** response styles. Initial starting date for incremental replication when no state file (bookmarks) exists yet. Example format 2022-06-10:23:10:10+1200.
- `source_search_field`: optional: used by the **offset**, **page**, and **hateoas_body** response style. This is a search/query parameter used by the API for an incremental replication.

  The difference between the `replication_key` and the `source_search_field` is the search field used in request parameters whereas the replication_key is the name of the field in the API reponse. Example if the source_search_field = **last-updated** the generated schema from the api discovery
  might be **meta_lastUpdated**. The replication_key is set to meta_lastUpdated, and the search_parameter to last-updated. Note: Please set the `replication_key`, `start_date`, `source_search_field`, and `source_search_query` parameters all together.
- `source_search_query`: optional: used by the **offset**, **page**, and **hateoas_body** response style. This is a query template to be issued against the API. A simple query template example for FHIR API's is **gt$last_run_date**.

  A more complex example against an Opensearch API, **{\\"bool\\": {\\"filter\\": [{\\"range\\": { \\"meta.lastUpdated\\": { \\"gt\\": \\"$last_run_date\\" }}}] }}**. Note: Any required double quotes in the query template must be escaped.

  At run-time, the tap will dynamically change the value **$last_run_date** with either the defined `start_date` parameter or the last bookmark (stream state) value.
  Example: source_search_field=**last-updated**, the
  source_search_query = **gt$last_run_date**, and the current replication state = 2022-08-10:23:10:10+1200.   At run time this creates a request parameter **last-updated=gt2022-06-10:23:10:10+1200**.

- `is_sorted`: optional: stream-level, boolean, default `False`. Set to `true` when the source API returns records ordered by the replication key (e.g. `sequence_id`, `created_at`). When `true`, the stream is declared sorted so interrupted syncs are resumable; the source API must actually return records ordered by the replication key. See [Meltano Singer SDK – Incremental replication](https://sdk.meltano.com/en/latest/incremental_replication.html).
- `pagination_stop_on_duplicate_token`: optional: when set on the stream, overrides the top-level `pagination_stop_on_duplicate_token` for JSONPath pagination (`jsonpath_paginator` / default request style). Default `false` at top level when omitted.

#### Top-Level Authentication config options.
- `auth_method`: optional: The method of authentication used by the API. Supported options
  include:
  - **oauth**: for OAuth2 authentication
  - **basic**: Basic Header authentication - base64-encoded username + password config items
  - **api_key**: for API Keys in the header e.g. X-API-KEY.
  - **bearer_token**: for Bearer token authentication.
  - **aws**: for AWS authentication. Works with the `aws_credentials` parameter.
  - Defaults to no_auth which will take authentication parameters passed via the headers config.
- `api_keys`: optional: A dictionary of API Key/Value pairs used by the api_key auth method
  Example: { "X-API-KEY": "my secret value"}.
- `client_id`: optional: Used for the OAuth2 authentication method. The public application ID
  that's assigned for Authentication. The **client_id** should accompany a **client_secret**.
- `client_secret`: optional: Used for the OAuth2 authentication method. The client_secret is a
  secret known only to the application and the authorization server. It is essential the
  application's own password.
- `username`: optional: Used for a number of authentication methods that use a user
  password combination for authentication.
- `password`: optional: Used for a number of authentication methods that use a user password
  combination for authentication.
- `bearer_token`: optional: Used for the Bearer Authentication method, which uses a token as part
  of the authorization header for authentication.
- `refresh_token`: optional: An OAuth2 Refresh Token is a string that the OAuth2 client can use to
  get a new access token without the user's interaction.
- `grant_type`: optional: Used for the OAuth2 authentication method. The grant_type is required
  to describe the OAuth2 flow. Flows support by this tap include **client_credentials**, **refresh_token**, **password**.
- `scope`: optional: Used for the OAuth2 authentication method. The scope is optional, it is a
  mechanism to limit the amount of access that is granted to an access token. One or more scopes
  can be provided delimited by a space.
- `access_token_url`: optional: Used for the OAuth2 authentication method. This is the end-point
  for the authentication server used to exchange the authorization codes for a access token.
- `redirect_uri`: optional: Used for the OAuth2 authentication method. This optional as the
  redirect_uri may be part of the token returned by the authentication server. If a redirect_uri
  is provided, it determines where the API server redirects the user after the user completes the
  authorization flow.
- `oauth_extras`: optional: A object of Key/Value pairs for additional oauth config parameters
  which may be required by the authorization server. Example: { "resource": "https://analysis.windows.net/powerbi/api" }.
- `oauth_expiration_secs`: optional: Used for OAuth2 authentication method. This optional setting
  is a timer for the expiration of a token in seconds. If not set the OAuth will use the default
  expiration set in the token by the authorization server.
- `aws_credentials`: optional: A object of Key/Value pairs to support AWS authentication when using the AWS authenticator. While the tap can use AWS [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html) environment variables and aws_profiles instead of supplying the keys and region, the [AWS service code](https://docs.aws.amazon.com/general/latest/gr/rande.html) needs to be specified e.g. `es` for OpenSearch / Elastic Search. By default the requirement to use `use_signed_credentials` is set to true. Config example:
  ```json
  { "aws_access_key_id": "my_aws_key_id",
    "aws_secret_access_key": "my_aws_secret_access_key",
    "aws_region": "us-east-1",
    "aws_service": "es",
    "use_signed_credentials": true}
  ```

#### Complex Authentication

The previous section showed out of the box methods for a single factor of authentication e.g. x-api-key, basic or oauth. If the API requires multiple forms of authentication, you may need to pass some of the authentication methods via the headers to be combined with the main auth_method.

Example:
An API may use OAuth2 for authentication but also requires an X-API-KEY to be supplied as well. In this situation pass the X-API-KEY as part of the `headers` config, and the rest of the config should be set for OAuth e.g.

- headers = '{"x-api-key": "my_secret_api_key"}'
- auth_method = "oauth"
- grant_type = "client_credentials"
- access_token_url = "https://auth.example.server/oauth2/token"
- client_id = "my_example_client_id"
- client_secret = "my_example_client_secret"

Some servers may require additional information like a `Request-Context` which is usually Base64 encoded. If this is the case it should be included in the `headers` config as well.

Example:

- headers = '{"x-api-key": "my_secret_api_key", "Request-Context": "my_example_Base64_encoded_json_object"}'

[← Installation](installation.md) · [Documentation index](index.md) · [Pagination →](pagination.md)
