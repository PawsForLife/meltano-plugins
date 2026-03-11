"""Tap implementation for REST API sources."""

import copy
import json
from typing import Any, List, Optional

import requests
from genson import SchemaBuilder
from singer_sdk import Tap
from singer_sdk import typing as th
from singer_sdk.authenticators import APIAuthenticatorBase
from singer_sdk.helpers.jsonpath import extract_jsonpath

from restful_api_tap.auth import ConfigurableOAuthAuthenticator, get_authenticator
from restful_api_tap.streams import DynamicStream
from restful_api_tap.utils import flatten_json


class RestfulApiTap(Tap):
    """REST API tap: extractor that reads from REST API sources and emits Singer messages."""

    name = "restful-api-tap"

    # Required by APIAuthenticatorBase; the Tap reads auth settings from the config file.
    tap_name = name

    # Caches the authenticator so the Tap does not hit the auth endpoint for each stream.
    _authenticator: Optional[APIAuthenticatorBase] = None

    common_properties = th.PropertiesList(
        th.Property(
            "path",
            th.StringType,
            required=False,
            description="Path appended to the source base URL (api_url). Stream-level "
            "path overwrites top-level path.",
        ),
        th.Property(
            "params",
            th.ObjectType(),
            default={},
            required=False,
            description="Object passed as params to requests (e.g. query string). "
            "Supplied via config file. Stream-level params are merged with "
            "top-level; stream-level overwrites same keys.",
        ),
        th.Property(
            "headers",
            th.ObjectType(),
            required=False,
            description="Headers for API requests. Supplied via config file. "
            "Stream-level headers are merged with top-level; stream-level "
            "overwrites same keys.",
        ),
        th.Property(
            "records_path",
            th.StringType,
            required=False,
            description="JSONPath in the API response that contains the records to emit "
            "as RECORD messages. Defaults to `$[*]`. Stream-level value "
            "overwrites top-level.",
        ),
        th.Property(
            "primary_keys",
            th.ArrayType(th.StringType),
            required=False,
            description="Property names that uniquely identify a record (key properties "
            "in Singer SCHEMA; primary_keys in the SDK).",
        ),
        th.Property(
            "replication_key",
            th.StringType,
            required=False,
            description="Property used for INCREMENTAL replication. The tap stores the "
            "last seen value in state (bookmarks) and uses it on the next run. "
            "Should be an incrementing integer or datetime.",
        ),
        th.Property(
            "except_keys",
            th.ArrayType(th.StringType),
            default=[],
            required=False,
            description="Keys (composite or not) that are not recursively flattened; "
            "their values are serialized as JSON. Lists in records are "
            "handled the same way so RECORD messages are not duplicated "
            "per list item.",
        ),
        th.Property(
            "num_inference_records",
            th.NumberType,
            default=50,
            required=False,
            description="Number of records used during Discovery to infer the stream "
            "schema. Defaults to 50.",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            required=False,
            description="Initial value when using a date-based replication key and no "
            "state file or bookmark is available.",
        ),
        th.Property(
            "source_search_field",
            th.StringType,
            required=False,
            description="Optional API query field for incremental sync (e.g. "
            "last-updated). Used with replication_key and source_search_query "
            "to resume from stream state (bookmark). Also set replication_key "
            "(API response field corresponding to this) and start_date.",
        ),
        th.Property(
            "source_search_query",
            th.StringType,
            required=False,
            description="Optional query template for the API. Use $last_run_date; at "
            "run time the tap replaces it with start_date or the last "
            "bookmark/stream state from the state file. Example (FHIR): "
            "gt$last_run_date. Opensearch example: "
            '{"bool": {"filter": [{"range": '
            '{"meta.lastUpdated": {"gt": "$last_run_date"}}}]}}. '
            "Escape any required double quotes in the template.",
        ),
        th.Property(
            "is_sorted",
            th.BooleanType(),
            default=False,
            required=False,
            description="When true, the stream is declared sorted by replication_key; "
            "enables resumable state if the sync is interrupted.",
        ),
    )

    top_level_properties = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType,
            required=True,
            description="Base URL for the API source.",
        ),
        th.Property(
            "auth_method",
            th.StringType,
            default="no_auth",
            required=False,
            description="Authentication method for the API (from config file). Options: "
            "oauth (OAuth2), basic (base64 username+password), api_key (e.g. "
            "X-API-KEY), bearer_token, aws. Defaults to no_auth (use headers).",
        ),
        th.Property(
            "api_keys",
            th.ObjectType(),
            required=False,
            description="A object of API Key/Value pairs used by the api_key auth "
            "method Example: { X-API-KEY: my secret value}.",
        ),
        th.Property(
            "client_id",
            th.StringType,
            required=False,
            description="Used for the OAuth2 authentication method. The public "
            "application ID that's assigned for Authentication. The "
            "client_id should accompany a client_secret.",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=False,
            description="Used for the OAuth2 authentication method. The client_secret "
            "is a secret known only to the application and the "
            "authorization server. It is essential the application's "
            "own password.",
        ),
        th.Property(
            "username",
            th.StringType,
            required=False,
            description="Used for a number of authentication methods that use a user "
            "password combination for authentication.",
        ),
        th.Property(
            "password",
            th.StringType,
            required=False,
            description="Used for a number of authentication methods that use a user "
            "password combination for authentication.",
        ),
        th.Property(
            "bearer_token",
            th.StringType,
            required=False,
            description="Used for the Bearer Authentication method, which uses a token "
            "as part of the authorization header for authentication.",
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            required=False,
            description="An OAuth2 Refresh Token is a string that the OAuth2 "
            "client can use to get a new access token without the user's "
            "interaction.",
        ),
        th.Property(
            "grant_type",
            th.StringType,
            required=False,
            description="Used for the OAuth2 authentication method. The grant_type "
            "is required to describe the OAuth2 flow. Flows support by "
            "this tap include client_credentials, refresh_token, password.",
        ),
        th.Property(
            "scope",
            th.StringType,
            required=False,
            description="Used for the OAuth2 authentication method. The scope is "
            "optional, it is a mechanism to limit the amount of access "
            "that is granted to an access token. One or more scopes can "
            "be provided delimited by a space.",
        ),
        th.Property(
            "access_token_url",
            th.StringType,
            required=False,
            description="Used for the OAuth2 authentication method. This is the "
            "end-point for the authentication server used to exchange "
            "the authorization codes for a access token.",
        ),
        th.Property(
            "redirect_uri",
            th.StringType,
            required=False,
            description="Used for the OAuth2 authentication method. This is optional "
            "as the redirect_uri may be part of the token returned by "
            "the authentication server. If a redirect_uri is provided, "
            "it determines where the API server redirects the user after "
            "the user completes the authorization flow.",
        ),
        th.Property(
            "oauth_extras",
            th.ObjectType(),
            required=False,
            description="A object of Key/Value pairs for additional oauth config "
            "parameters which may be required by the authorization server."
            "Example: "
            "{resource: https://analysis.windows.net/powerbi/api}.",
        ),
        th.Property(
            "oauth_expiration_secs",
            th.IntegerType,
            default=None,
            required=False,
            description="Used for OAuth2 authentication method. This optional "
            "setting is a timer for the expiration of a token in "
            "seconds. If not set the OAuth will use the default "
            "expiration set in the token by the authorization server.",
        ),
        th.Property(
            "aws_credentials",
            th.ObjectType(),
            default=None,
            required=False,
            description="An object of aws credentials to authenticate to access AWS "
            "services. This example is to access the AWS OpenSearch "
            "service. Example: { aws_access_key_id: my_aws_key_id, "
            "aws_secret_access_key: my_aws_secret_access_key, "
            "aws_region: us-east-1, "
            "aws_service: es, use_signed_credentials: true} ",
        ),
        th.Property(
            "next_page_token_path",
            th.StringType,
            default=None,
            required=False,
            description="JSONPath to the token for the next page of results. "
            "Defaults to `$.next_page`.",
        ),
        th.Property(
            "pagination_request_style",
            th.StringType,
            default="default",
            required=False,
            description="the pagination style to use for requests. "
            "Defaults to `default`",
        ),
        th.Property(
            "pagination_response_style",
            th.StringType,
            default="default",
            required=False,
            description="the pagination style to use for response. "
            "Defaults to `default`",
        ),
        th.Property(
            "use_request_body_not_params",
            th.BooleanType,
            default=False,
            required=False,
            description="sends the request parameters in the request body."
            "This is normally not required, a few API's like OpenSearch"
            "require this. Defaults to `False`",
        ),
        th.Property(
            "backoff_type",
            th.StringType,
            default=None,
            required=False,
            allowed_values=[None, "message", "header"],
            description="The style of Backoff applied to rate limited APIs."
            "None: Default Meltano SDK backoff_wait_generator, message: Scans "
            "the response message for a time interval, header: retrieves the "
            "backoff value from a header key response."
            " Defaults to `None`",
        ),
        th.Property(
            "backoff_param",
            th.StringType,
            default="Retry-After",
            required=False,
            description="The name of the key which contains a the "
            "backoff value in the response. This is very applicable to backoff"
            " values in headers. Defaults to `Retry-After`",
        ),
        th.Property(
            "backoff_time_extension",
            th.IntegerType,
            default=0,
            required=False,
            description="A time extension (in seconds) to add to the backoff "
            "value from the API plus jitter. Some APIs are not precise"
            ", this adds an additional wait delay. Defaults to `0`",
        ),
        th.Property(
            "store_raw_json_message",
            th.BooleanType,
            default=False,
            required=False,
            description="When true, add _SDC_RAW_JSON to each RECORD payload with the "
            "raw incoming message. Useful when the schema is not well defined. "
            "Defaults to False. When flatten_records is False the raw row is "
            "stored by reference (downstream must not mutate it).",
        ),
        th.Property(
            "flatten_records",
            th.BooleanType,
            default=False,
            required=False,
            description="When true, flatten records and infer schema from flattened "
            "sample; when false, preserve nested structure.",
        ),
        th.Property(
            "pagination_page_size",
            th.IntegerType,
            default=None,
            required=False,
            description="Number of records per page for paginated streams. Defaults to None.",
        ),
        th.Property(
            "pagination_results_limit",
            th.IntegerType,
            default=None,
            required=False,
            description="Maximum number of records to fetch per stream. Defaults to None.",
        ),
        th.Property(
            "pagination_next_page_param",
            th.StringType,
            default=None,
            required=False,
            description="The name of the param that indicates the page/offset. "
            "Defaults to None",
        ),
        th.Property(
            "pagination_limit_per_page_param",
            th.StringType,
            default=None,
            required=False,
            description="The name of the param that indicates the limit/per_page. "
            "Defaults to None",
        ),
        th.Property(
            "pagination_total_limit_param",
            th.StringType,
            default="total",
            required=False,
            description="The name of the param that indicates the total limit e.g. "
            "total, count. Defaults to total",
        ),
        th.Property(
            "pagination_initial_offset",
            th.IntegerType,
            default=1,
            required=False,
            description="The initial offset to start pagination from. Defaults to 1",
        ),
        th.Property(
            "offset_records_jsonpath",
            th.StringType,
            default=None,
            required=False,
            description="Optional jsonpath string representing the path in the results "
            "Defaults to `None`.",
        ),
        th.Property(
            "discovery_request_limit",
            th.IntegerType,
            default=None,
            required=False,
            description="Limits the number of records requested during Discovery "
            "(schema inference). Passed via discovery_limit_param to reduce "
            "API response size. Ignored when schema is from a path or dict.",
        ),
        th.Property(
            "discovery_limit_param",
            th.StringType,
            default="limit",
            required=False,
            description="Query param name used with discovery_request_limit during "
            "Discovery (e.g. 'limit', 'per_page', 'size'). Defaults to 'limit'.",
        ),
    )

    # add common properties to top-level properties
    for prop in common_properties.wrapped.values():
        top_level_properties.append(prop)

    # add common properties to the stream schema
    stream_properties = th.PropertiesList()
    stream_properties.wrapped = copy.copy(common_properties.wrapped)
    stream_properties.append(
        th.Property(
            "name", th.StringType, required=True, description="Name of the stream."
        ),
    )
    stream_properties.append(
        th.Property(
            "schema",
            th.CustomType(
                {"anyOf": [{"type": "string"}, {"type": "null"}, {"type:": "object"}]}
            ),
            required=False,
            description="Valid Singer schema (for SCHEMA messages) or path to a "
            ".json file containing one. If provided, schema is not inferred "
            "during Discovery.",
        ),
    )

    # add streams schema to top-level properties
    top_level_properties.append(
        th.Property(
            "streams",
            th.ArrayType(th.ObjectType(*stream_properties.wrapped.values())),
            required=False,
            description="Array of stream definitions (name, path, optional schema, "
            "replication_key, etc.) for the catalog.",
        ),
    )

    config_jsonschema = top_level_properties.to_dict()

    def discover_streams(self) -> List[DynamicStream]:  # type: ignore
        """Build the list of streams for Discovery. Returns stream instances used to build the catalog.

        Returns:
            List of DynamicStream instances.

        """
        # print(self.top_level_properties.to_dict())

        streams = []
        for stream in self.config["streams"]:
            # resolve config
            records_path = stream.get(
                "records_path", self.config.get("records_path", "$[*]")
            )
            except_keys = stream.get("except_keys", self.config.get("except_keys", []))
            path = stream.get("path", self.config.get("path", ""))
            params = {**self.config.get("params", {}), **stream.get("params", {})}
            headers = {**self.config.get("headers", {}), **stream.get("headers", {})}
            start_date = stream.get("start_date", self.config.get("start_date", ""))
            replication_key = stream.get(
                "replication_key", self.config.get("replication_key", "")
            )
            source_search_field = stream.get(
                "source_search_field", self.config.get("source_search_field", "")
            )
            source_search_query = stream.get(
                "source_search_query", self.config.get("source_search_query", "")
            )
            offset_records_jsonpath = stream.get(
                "offset_records_jsonpath",
                self.config.get("offset_records_jsonpath", None),
            )
            # Stream overrides top-level for flatten_records.
            flatten_records = stream.get(
                "flatten_records", self.config.get("flatten_records", False)
            )
            is_sorted = stream.get("is_sorted", False)

            schema = {}
            schema_config = stream.get("schema")
            if isinstance(schema_config, str):
                self.logger.info("Found path to a schema, not doing discovery.")
                with open(schema_config, "r") as f:
                    schema = json.load(f)

            elif isinstance(schema_config, dict):
                self.logger.info("Found schema in config, not doing discovery.")
                builder = SchemaBuilder()
                builder.add_schema(schema_config)
                schema = builder.to_schema()

            else:
                self.logger.info("No schema found. Inferring schema from API call.")
                schema = self.get_schema(
                    records_path,
                    except_keys,
                    stream.get(
                        "num_inference_records",
                        self.config["num_inference_records"],
                    ),
                    path,
                    params,
                    headers,
                    flatten_records=flatten_records,
                )

            streams.append(
                DynamicStream(
                    tap=self,
                    name=stream["name"],
                    path=path,
                    params=params,
                    headers=headers,
                    records_path=records_path,
                    primary_keys=stream.get(
                        "primary_keys", self.config.get("primary_keys", [])
                    ),
                    replication_key=replication_key,
                    except_keys=except_keys,
                    next_page_token_path=self.config.get("next_page_token_path"),
                    pagination_request_style=self.config["pagination_request_style"],
                    pagination_response_style=self.config["pagination_response_style"],
                    pagination_page_size=self.config.get("pagination_page_size"),
                    pagination_results_limit=self.config.get(
                        "pagination_results_limit"
                    ),
                    pagination_next_page_param=self.config.get(
                        "pagination_next_page_param"
                    ),
                    pagination_limit_per_page_param=self.config.get(
                        "pagination_limit_per_page_param"
                    ),
                    pagination_total_limit_param=self.config.get(
                        "pagination_total_limit_param"
                    ),
                    pagination_initial_offset=self.config.get(
                        "pagination_initial_offset",
                        1,
                    ),
                    offset_records_jsonpath=offset_records_jsonpath,
                    schema=schema,
                    start_date=start_date,
                    source_search_field=source_search_field,
                    source_search_query=source_search_query,
                    is_sorted=is_sorted,
                    use_request_body_not_params=self.config.get(
                        "use_request_body_not_params"
                    ),
                    backoff_type=self.config.get("backoff_type"),
                    backoff_param=self.config.get("backoff_param"),
                    backoff_time_extension=self.config.get("backoff_time_extension"),
                    store_raw_json_message=self.config.get("store_raw_json_message"),
                    flatten_records=flatten_records,
                    authenticator=self._authenticator,
                )
            )

        return streams

    def get_schema(
        self,
        records_path: str,
        except_keys: list,
        inference_records: int,
        path: str,
        params: dict,
        headers: dict,
        flatten_records: bool = False,
    ) -> Any:
        """Infer stream schema from sample records (Discovery). Uses config file for auth and optional discovery_request_limit.

        Result is used for SCHEMA messages and the catalog. The full Discovery response
        is held in memory; use discovery_request_limit (and discovery_limit_param)
        when the API supports it to limit response size.

        If auth_method is set, get_authenticator obtains credentials from the config
        file; it caches the authenticator in self._authenticator and sets self.http_auth
        when required.

        Args:
            records_path: See config_jsonschema.
            except_keys: See config_jsonschema.
            inference_records: See config_jsonschema.
            path: See config_jsonschema.
            params: See config_jsonschema.
            headers: See config_jsonschema.
            flatten_records: When true, flatten sample records before inference; when
                false, infer from raw nested records.

        Raises:
            ValueError: If the response is not valid or a record is not valid JSON.

        Returns:
            JSON Schema for the stream (Singer SCHEMA message).

        """
        # TODO: this request format is not very robust

        # Initialise Variables
        auth_method = self.config.get("auth_method", "")
        self.http_auth = None

        if auth_method and not auth_method == "no_auth":
            # Obtain authenticator from config for Discovery request.
            get_authenticator(self)

            # Get an initial oauth token if an oauth method
            if auth_method == "oauth" and isinstance(
                self._authenticator, ConfigurableOAuthAuthenticator
            ):
                self._authenticator.get_initial_oauth_token()

            headers.update(getattr(self._authenticator, "auth_headers", {}))
            params.update(getattr(self._authenticator, "auth_params", {}))

        # Limit Discovery response size when the API supports it (reduces memory).
        discovery_limit = self.config.get("discovery_request_limit")
        if discovery_limit is not None:
            param_name = self.config.get("discovery_limit_param", "limit")
            params = {**params, param_name: discovery_limit}

        r = requests.get(
            self.config["api_url"] + path,
            auth=self.http_auth,
            params=params,
            headers=headers,
        )
        if r.ok:
            records = extract_jsonpath(records_path, input=r.json())
        else:
            self.logger.error(f"Error Connecting, message = {r.text}")
            raise ValueError(r.text)

        builder = SchemaBuilder()
        builder.add_schema(th.PropertiesList().to_dict())
        for i, record in enumerate(records):
            if type(record) is not dict:
                self.logger.error("Input must be a dict object.")
                raise ValueError("Input must be a dict object.")

            if flatten_records:
                flat_record = flatten_json(
                    record, except_keys, store_raw_json_message=False
                )
                builder.add_object(flat_record)
            else:
                builder.add_object(record)
            # Optionally add _sdc_raw_json to RECORD payload for raw message storage
            if self.config.get("store_raw_json_message"):
                builder.add_object({"_sdc_raw_json": {}})

            if i >= inference_records:
                break

        self.logger.debug(f"{builder.to_json(indent=2)}")
        return builder.to_schema()
