# Pagination

[← Configuration](configuration.md) · [Documentation index](index.md) · [Examples →](examples.md)

API Pagination is a complex topic as there is no real single standard, and many different implementations.  Unless options are provided, both the request and results style type default to the `default`, which is the pagination style originally implemented. Where possible, this tap utilises the Meltano SDK paginators https://sdk.meltano.com/en/latest/reference.html#pagination .

### Default Request Style
The default request style for pagination is using a `JSONPath Paginator` to locate the next page token.

### Default Response Style
The default response style for pagination is described below:
- If there is a token, add that as a `page` URL parameter.

### Additional Request / Paginator Styles
There are additional request styles supported as follows for pagination.
- `jsonpath_paginator` or `default` - This style obtains the token for the next page from a specific location in the response body via JSONPath notation. In many situations the `jsonpath_paginator` is a more appropriate paginator to the `hateoas_paginator`.
  - `next_page_token_path` - The jsonpath to next page token. Example: `"$['@odata.nextLink']"`, this locates the token returned via the Microsoft Graph API. Default `'$.next_page'` for the `jsonpath_paginator` paginator only otherwise None.
  - `pagination_stop_on_duplicate_token` - Top-level or stream-level boolean (see [configuration](configuration.md)). When `true`, pagination stops if the next token equals the current token instead of raising a loop error. Default `false`. Use when the source repeats the last cursor (e.g. last record’s id) on the final page while still returning HTTP 200—common for cursor/`after`-style APIs such as Medallia sequence-id pagination.
- `offset_paginator` or `style1` - This style uses URL parameters named offset and limit
  - `offset` is calculated from the previous response, or not set if there is no previous response
  - `pagination_page_size` - Sets a limit to number of records per page / response. Default `25` records.
  - `pagination_limit_per_page_param` - the name of the API parameter to limit number of records per page. Default parameter name `limit`.
  - `pagination_total_limit_param` - The name of the param that indicates the total limit e.g. total, count. Defaults to total
  - `next_page_token_path` - Used to locate an appropriate link in the response. Default None - but looks in the `pagination` section of the JSON response by default. Example, jsonpath to get the offset from the NOAA API `'$.metadata.resultset'`.
  - `pagination_initial_offset` - The initial offset for the first request. Defaults to 1.
- `simple_header_paginator` - This style uses links in the Header Response to locate the next page. Example the `x-next-page` link used by the Gitlab API.
- `header_link_paginator` - This style uses the default header link paginator from the Meltano SDK.
- `restapi_header_link_paginator` - This style is a variant on the header_link_paginator. It supports the ability to read from GitHub API.
  - `pagination_page_size` - Sets a limit to number of records per page / response. Default `25` records.
  - `pagination_limit_per_page_param` - the name of the API parameter to limit number of records per page. Default parameter name `per_page`.
  - `pagination_results_limit` - Restricts the total number of records returned from the API. Default None i.e. no limit.
- `hateoas_paginator` - This style parses the next_token response for the parameters to pass. It is used by API's utilising the HATEOAS Rest style [HATEOAS](https://en.wikipedia.org/wiki/HATEOAS), including [FHIR API's](https://hl7.org/fhir/http.html).
  - `pagination_page_size` - Sets a limit to number of records per page / response. Default None.
  - `pagination_limit_per_page_param` - the name of the API parameter to limit number of records per page e.g. `_count` for [FHIR API's](https://hl7.org/fhir/http.html). Default None.
- `single_page_paginator` - A paginator that does works with single-page endpoints.
- `page_number_paginator` - Paginator class for APIs that use page number. Looks at the response link to determine more pages.
  - `next_page_token_path` - Use to locate an appropriate link in the response. Default `"hasMore"`.
  - `pagination_initial_offset` - Use to set the initial page number. Default `1`.
- `simple_offset_paginator` - A paginator that uses `offset` and `limit` parameters to page through a collection of resources. Unlike `offset_paginator`, this paginator does not rely on any headers to determine whether it should keep paginating. Instead, it will continue paginating (by sending requests with increasing `offset`) until the API returns 0 results. You can use this paginator if the API returns a JSON array of records rather than a top-level object.
  - `pagination_page_size` - Sets a limit to number of records per page / response. Default `25` records.
  - `offset_records_jsonpath` - The JSONPath to the records in the response. Defaults to `None`. In the example below we would select the contacts array with `"offset_records_jsonpath": "$.contacts"`. Once the number of records doe not equal `pagination_page_size` the tap will stop paginating.

    ```json
    {
      "contacts": [
        {
          "id": 52,
          "emailBlacklisted": false,
          "smsBlacklisted": false,
          "createdAt": "2024-09-24T01:00:00.000-00:00",
          "modifiedAt": "2024-09-25T01:00:00.000-00:00",
        }
      ],
      "count": 256
    }
    ```

### Additional Response Styles
There are additional response styles supported as follows.
- `default` or `page` - This style uses page style offsets params to identify the next page.
- `offset` or `style1` - This style retrieves pagination information by default from the `pagination` top-level element in the response.  Expected format is as follows:
    ```json
    "pagination": {
        "total": 136,
        "limit": 2,
        "offset": 2
    }
    ```
  The next page token, which in this case is really the next starting record number, is calculated by the limit, current offset, or None is returned to indicate no more data.  For this style, the response style _must_ include the limit in the response, even if none is specified in the request, as well as ( `total` or `count` ) and offset to calculate the next token value.

  It is expected that this API Response Style will be used with request style of `offset_paginator` or `style1`.
  - The `next_page_token_jsonpath` can be used to provide a JSONPath location to the pagination location e.g. `'$.metadata.resultset'`. Default `pagination` from the tap-level element in the response.
- `header_link` - This style parses the next page link in the Header Response. It is expected that this response will be used with an appropriate request style e.g. `restapi_header_link_paginator`.
  - `pagination_page_size` - Sets a limit to number of records per page / response. Default `25` records.
  - `pagination_limit_per_page_param` - the name of the API parameter to limit number of records per page. Default parameter name `per_page`.
  - `pagination_results_limit` - Restricts the total number of records returned from the API. Default None i.e. no limit.
- `hateoas_body` - This style requires a well crafted `next_page_token_path` configuration
  parameter to retrieve the request parameters from the GET request response for a subsequent request.

### JSON Path for extracting tokens
  The `next_page_token_path` and `records_path` use JSONPath to locate sections within the request reponse.

  The following example extracts the URL for the next pagination page.
    ```json
    "next_page_token_path": "$.link[?(@.relation=='next')].url."
    ```

  The following example demonstrates the power of JSONPath extensions by further splitting the URL and extracting just the parameters. Note: This is not required for FHIR API's but is provided for illustration of added functionality for complex use cases.
    ```json
    "next_page_token_path": "$.link[?(@.relation=='next')].url.`split(?, 1, 1)`"
    ```
  The [JSONPath Evaluator](https://jsonpath.com/) website is useful to test the correct json path expression to use.

  Example json response from a FHIR API.


    ```json
    {
      "resourceType": "Bundle",
      "id": "44f2zf06-g53c-4218-a3ef-08bb6c2fde4a",
      "meta": {
        "lastUpdated": "2022-06-28T18:25:01.165+12:00"
      },
      "type": "searchset",
      "total": 63,
      "link": [
        {
          "relation": "self",
          "url": "https://myexample_fhir_api_url/base_folder/ExampleService?_count=10&_getpageoffset=10&services-provided-type=MY_INITIAL_EXAMPLE_SERVICE"
        },
        {
          "relation": "next",
          "url": "https://myexample_fhir_api_url/base_folder?_getpages=44f2zf06-g53c-4218-a3ef-08bb6c2fde4a&_getpagesoffset=10&_count=10&_pretty=true&_bundletype=searchset"
        }
      ],
      "entry": [
        {
          "fullUrl": "https://myexample_fhir_api_url/base_folder/ExampleService/example-service-123456",
          "resource": {
            "resourceType": "ExampleService",
            "id": "example-service-123456"
          }
        }
      ]
  }
    ```

  Note: If you wish to extract the body from example GET request response above the following configuration parameter `records_path` will return the actual json content.
  ```json
  "records_path": "$.entry[*].resource"
  ```

[← Configuration](configuration.md) · [Documentation index](index.md) · [Examples →](examples.md)
