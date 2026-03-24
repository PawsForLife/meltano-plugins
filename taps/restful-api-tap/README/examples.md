# Example settings for different API's

[← Pagination](pagination.md) · [Documentation index](index.md) · [Usage →](usage.md)

This section provides examples of settings for accessing different API's. The tap configuration examples are provided in the form of environment variables. You can supply a config file (e.g. [config.json](../config.sample.json)) instead of environment variables.

Where config values are marked with `<removed .. >`, replace the text with your Authentication and API config.

### Microsoft Graph API v1.0

This example uses the `jsonpath paginator`. In this example, it requires a Microsoft Azure AD admin to register an APP to obtain an OAuth Token to perform an OAuth flow with the Microsoft Graph API. The details below may be different based on your setup, adjust accordingly.

Result: Two streamed datasets, one `whoami` a simple json response about yourself, two a sharepoint list `my_sharepoint_list`.

```
# Access MSOFFICE objects via the GraphAPI
export RESTFUL_API_TAP_API_URL=https://graph.microsoft.com
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="jsonpath_paginator"
export RESTFUL_API_TAP_PAGINATION_RESPONSE_STYLE="hateoas_body"
export RESTFUL_API_TAP_NEXT_PAGE_TOKEN_PATH="$['@odata.nextLink']"
export RESTFUL_API_TAP_START_DATE="2001-01-01T00:00:00.00+12:00"
export RESTFUL_API_TAP_AUTH_METHOD="oauth"
export RESTFUL_API_TAP_USERNAME="<removed place in UPN/email address>"
export RESTFUL_API_TAP_PASSWORD="<removed place in password>"
export RESTFUL_API_TAP_GRANT_TYPE="password"
export RESTFUL_API_TAP_ACCESS_TOKEN_URL="https://login.microsoftonline.com/<removed place in Azure AAD APP ID>/oauth2/v2.0/token"
export RESTFUL_API_TAP_CLIENT_ID="<removed place in OAuth Client ID>"
export RESTFUL_API_TAP_CLIENT_SECRET="<removed place in OAuth Client Secret>"
export RESTFUL_API_TAP_SCOPE="<removed place in client scope url e.g. https://graph.microsoft.com/user.read>"
export RESTFUL_API_TAP_STREAMS='[{"name": "whoami", "path": "/v1.0/me", "primary_keys": ["id"]},{"name": "my_sharepoint_list", "path": "/v1.0/sites/<removed place in SharePoint Site ID>/Lists/<removed place in SharePoint list id>/items/?expand=columns,items(expand=fields)", "primary_keys": ["id"], "records_path": "$.value[*].fields"}]'
```

### Gitlab API

This example uses the `simple header paginator` and returns 50 records from the Gitlab API for Projects. Note: There is an exception raised due to the 50 record limit - this is an example hence the limit.

```
# Access Gitlab projects via the GitLab API
export RESTFUL_API_TAP_API_URL=https://gitlab.com/api/v4/projects
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="simple_header_paginator"
export RESTFUL_API_TAP_PAGINATION_RESULTS_LIMIT=50
export RESTFUL_API_TAP_STREAMS='[{"name": "gitlab_projects", "primary_keys": ["id"]}]'
```

You could authenticate to Gitlab using a Personal Access Token (PAT) by adding this config.
```
export RESTFUL_API_TAP_HEADERS='{"Authorization": "Bearer <removed PAT bearer token>"}'
```

### GitHub API

This example uses the `headerlink paginator` and returns approximately 250 records from the GitHub API for Projects.

```
# Access GitHub users via the GitHub API
export RESTFUL_API_TAP_API_URL=https://api.github.com/users
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="restapi_header_link_paginator"
export RESTFUL_API_TAP_PAGINATION_RESPONSE_STYLE="header_link"
export RESTFUL_API_TAP_PAGINATION_PAGE_SIZE=50
export RESTFUL_API_TAP_PAGINATION_RESULTS_LIMIT=250
export RESTFUL_API_TAP_STREAMS='[{"name": "github_users", "primary_keys": ["id"]}]'
```

You could authenticate to GitHub using a Personal Access Token (PAT) by adding this config.
```
export RESTFUL_API_TAP_HEADERS='{"Authorization": "Bearer <removed PAT bearer token>"}'
```

### FHIR API

This example uses the `jsonpath paginator` to access a FHIR API. It uses the `hateoas response style` to process the next tokens.

This particular configuration will do an intial load of all data for a given resource defined in the `streams` config from the 01-Jan-2001. It will in subsequent runs incrementally pull changed data based on the lastUpdated timestamp by searching for records greater than the highest last updated timestamp. In this example the PlanDefinition FHIR resource is being extracted.

You will need appropriate OAuth Token details provided by the Administrator of the API.

```
export RESTFUL_API_TAP_API_URL=<remove put in the FHIR API url>
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="jsonpath_paginator"
export RESTFUL_API_TAP_PAGINATION_RESPONSE_STYLE="hateoas_body"
export RESTFUL_API_TAP_NEXT_PAGE_TOKEN_PATH="$.link[?(@.relation=='next')].url"
export RESTFUL_API_TAP_START_DATE="2001-01-01T00:00:00.00+12:00"
export RESTFUL_API_TAP_AUTH_METHOD="oauth"
export RESTFUL_API_TAP_GRANT_TYPE="client_credentials"
export RESTFUL_API_TAP_ACCESS_TOKEN_URL="https://login.microsoftonline.com/<removed place in Azure AAD APP ID>/oauth2/v2.0/token"
export RESTFUL_API_TAP_CLIENT_ID="<removed place in OAuth Client ID>"
export RESTFUL_API_TAP_CLIENT_SECRET="<removed place in OAuth Client Secret>"
export RESTFUL_API_TAP_SCOPE="<removed place in client scope url>"
export RESTFUL_API_TAP_STREAMS='[{"name":"plan_definition","path":"/PlanDefinition","primary_keys":["id"],"records_path":"$.entry[*].resource","replication_key":"meta_lastUpdated","search_parameter":"_lastUpdated","source_search_query": "gt$last_run_date"}]'
```

### NOAA API Example

This example uses the `offset paginator` to access the NOAA API to return location categories. In this example the offset tokens are not in the default location of `pagination` so the `next_page_token_path` is set to the NOAA API offset location in the json response i.e. `'$.metadata.resultset'`. This example also sets a limit parameter in the `streams` to only return 5 records at a time to prove the pagination is working.

```
# Access Locations Categories objects via the NOAA API
export RESTFUL_API_TAP_API_URL=https://www.ncei.noaa.gov/cdo-web/api/v2
export RESTFUL_API_TAP_HEADERS='{"token": "<enter NOAA token>"}'
export RESTFUL_API_TAP_NEXT_PAGE_TOKEN_PATH='$.metadata.resultset'
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="offset_paginator"
export RESTFUL_API_TAP_PAGINATION_RESPONSE_STYLE="style1"
export RESTFUL_API_TAP_PAGINATION_TOTAL_LIMIT_PARAM="count"
export RESTFUL_API_TAP_STREAMS='[{"name": "locationcategories", "params": {"limit": "5"}, "path": "/locationcategories", "primary_keys": ["id"], "records_path": "$.results[*]"}]'
```

### dbt Cloud API Example

This example uses the `offset paginator` to access the dbt Cloud API to return location categories. In this example the offset tokens are not in the default location of `pagination` so the `next_page_token_path` is set to the dbt API offset location in the json response i.e. `'$.extra'`. This example also sets the streams record_path to `"$.data[*]"` which is the location of the data.

```
# Access Locations Categories objects via the dbt Cloud API
# Access Gitlab objects via the dbt Cloud API
export RESTFUL_API_TAP_API_URL=https://<removed your url>.getdbt.com/api/v2/accounts/<removed account id>
export RESTFUL_API_TAP_HEADERS='{"Authorization": "Bearer <removed place in bearer token>"}'
export RESTFUL_API_TAP_NEXT_PAGE_TOKEN_PATH='$.extra'
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="offset_paginator"
export RESTFUL_API_TAP_PAGINATION_RESPONSE_STYLE="style1"
export RESTFUL_API_TAP_PAGINATION_TOTAL_LIMIT_PARAM="total_count"
export RESTFUL_API_TAP_STREAMS='[{"name": "jobs", "path": "/jobs", "primary_keys": ["id"], "records_path": "$.data[*]"}]'
```

### AWS OpenSearch API Example

This complex example uses the [AWS4Auth](https://github.com/tedder/requests-aws4auth) authenticator to provide signed AWS credentials in the requests to the AWS OpenSearch API endpoint. The `auth_method` is set to 'aws', and the required `aws_credentials` are provided.

Note: The AWS authentication does support [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html) environment variables and aws_profiles.

For pagination, the next page token is located in the **last** returned record. Using JSON Path the appropriate token response can be extracted via '$.hits.hits[-1:].sort' (-1 selects the last record in the array) and this is set in the `next_page_token_path` config setting. The API parameter used to select the next page is 'search_after' and this is set in the `pagination_next_page_param` config setting. To enable pagination in OpenSearch an API parameter named 'sort' must be set to a unique key e.g. '_id'. The number of records to returned per page is controlled via an API parameter called 'size'.

The OpenSearch API has a complex incremental replication query which must be sent in the request body. This is enabled by setting the `use_request_body_not_params` to True.

Finally set the replication suite of config settings ( `start_date`, `replication_key`, `source_search_field`, and `source_search_query` ) to enable incremental replication of data since the last run. For OpenSearch there is a complex query template which must be set in the streams `source_search_query` config setting.

Unlike most API requests, the API query is against an API parameter named `query` rather than the name of the API field. For this reason the `source_search_field` is set to 'query' in the streams array. Additionally, the streams record_path to `"$.hits.hits[*]"` which is the location of the records in the requests response.

```
# Access AWS objects via the AWS Open/Elastic Search API
export RESTFUL_API_TAP_API_URL="https://<endpoint>.<aws region>.<aws service>.amazonaws.com"
export RESTFUL_API_TAP_AWS_CREDENTIALS='{"aws_access_key_id": "<removed aws access key id>", "aws_secret_access_key": "removed aws secret access key>", "aws_region": "<aws region e.g. us‑east‑1>", "aws_service": "<aws service e.g. es for opensearch>", "create_signed_credentials": true}'
export RESTFUL_API_TAP_START_DATE="2001-01-01T00:00:00.00+12:00"
export RESTFUL_API_TAP_PAGINATION_REQUEST_STYLE="jsonpath_paginator"
export RESTFUL_API_TAP_PAGINATION_RESPONSE_STYLE="offset"
export RESTFUL_API_TAP_USE_REQUEST_BODY_NOT_PARAMS=true
export RESTFUL_API_TAP_NEXT_PAGE_TOKEN_PATH='$.hits.hits[-1:].sort'
export RESTFUL_API_TAP_PAGINATION_NEXT_PAGE_PARAM="search_after"
export RESTFUL_API_TAP_AUTH_METHOD='aws'
export RESTFUL_API_TAP_STREAMS='[{"name": "careplan", "params": {"size": 100, "sort": "_id"}, "path": "/careplan/_search", "primary_keys": [], "records_path": "$.hits.hits[*]", "replication_key": "_source_meta_lastUpdated", "source_search_field": "query", "source_search_query": "{\"bool\": {\"filter\": [{\"range\": { \"meta.lastUpdated\": { \"gt\": \"$last_run_date\" }}}] }}"}]'
```

[← Pagination](pagination.md) · [Documentation index](index.md) · [Usage →](usage.md)
