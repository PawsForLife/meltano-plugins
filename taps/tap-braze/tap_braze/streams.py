"""Braze REST API streams.

The tap pairs each Braze *list* endpoint (the campaign/canvas index, returning
ids plus light metadata) with the matching *details* endpoint (the descriptive
attributes: type, schedule, channels, messages, tags, timestamps). The details
endpoints accept a single id per call, so they are modelled as Singer SDK
child streams: each id emitted by a parent list stream fans out one details
request via ``parent_stream_type`` + ``get_child_context``.
"""

from __future__ import annotations

from collections.abc import Generator, Iterable, Mapping
from typing import Any

import requests
from singer_sdk import typing as th
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.pagination import (
    BaseAPIPaginator,
    PageNumberPaginator,
    SinglePagePaginator,
)
from singer_sdk.streams import RESTStream


class BrazeListPaginator(PageNumberPaginator):
    """Advance Braze 0-indexed ``page`` pagination.

    Braze list endpoints return up to 100 records under a fixed key and an
    empty array once exhausted; they send no ``hasMore`` flag or next-page
    token, so termination is inferred from an empty records array.
    """

    def __init__(self, start_value: int, records_key: str) -> None:
        """Remember which response key holds the records array."""
        super().__init__(start_value)
        self._records_key = records_key

    def has_more(self, response: requests.Response) -> bool:
        """Continue while the page carries records; stop on the empty page."""
        return bool(_records(response, self._records_key))


class BrazeStream(RESTStream):
    """Base stream for the Braze REST API."""

    @property
    def url_base(self) -> str:
        """Return the configured Braze REST instance URL."""
        return str(self.config["api_url"]).rstrip("/")

    @property
    def http_headers(self) -> dict[str, str]:
        """Authenticate with the configured REST API key as a bearer token."""
        return {"Authorization": f"Bearer {self.config['api_key']}"}

    def backoff_wait_generator(self) -> Generator[float]:
        """Use Retry-After when Braze rate-limits a request."""
        return self.backoff_runtime(value=_retry_after_seconds)

    def backoff_jitter(self, value: float) -> float:
        """Preserve the server-requested Retry-After duration exactly."""
        return value


class BrazeListStream(BrazeStream):
    """Base full-table Braze list stream.

    Subclasses set ``name``, ``path``, ``records_key`` (the response array that
    holds the list rows and drives pagination), and ``schema``.
    """

    primary_keys = ("id",)
    replication_method = "FULL_TABLE"
    records_key: str

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Return a fresh page-number paginator for each sync."""
        return BrazeListPaginator(start_value=0, records_key=self.records_key)

    def get_url_params(
        self,
        context: Mapping[str, Any] | None,
        next_page_token: int | None,
    ) -> dict[str, Any]:
        """Request the current 0-indexed page."""
        return {"page": next_page_token or 0}

    def parse_response(self, response: requests.Response) -> Iterable[dict[str, Any]]:
        """Yield records from the stream's list envelope."""
        yield from _records(response, self.records_key)


class BrazeDetailsStream(BrazeStream):
    """Base full-table Braze details child stream.

    One request per parent id. The details payload does not echo the id, so it
    is injected from the parent context and used as the primary key. Subclasses
    set ``name``, ``path``, ``parent_stream_type``, ``id_param`` (the query
    parameter naming the id), ``id_key`` (the injected context/record key), and
    ``schema``.
    """

    replication_method = "FULL_TABLE"
    id_param: str
    id_key: str

    def get_new_paginator(self) -> SinglePagePaginator:
        """Return a single-page paginator; details is one object per id."""
        return SinglePagePaginator()

    def get_url_params(
        self,
        context: Mapping[str, Any] | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        """Request the details for the single parent id in context."""
        if context is None or self.id_key not in context:
            raise ValueError(
                f"{self.name} requires {self.id_key} from its parent stream"
            )
        return {self.id_param: context[self.id_key]}

    def parse_response(self, response: requests.Response) -> Iterable[dict[str, Any]]:
        """Yield the single details object, dropping the API status envelope."""
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Braze {self.name} response must be an object")
        payload.pop("message", None)
        yield payload

    def post_process(
        self, row: dict[str, Any], context: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Stamp the parent id onto the record so it has a primary key."""
        if context is None or self.id_key not in context:
            raise ValueError(
                f"{self.name} requires {self.id_key} from its parent stream"
            )
        row[self.id_key] = context[self.id_key]
        return row


class CampaignsStream(BrazeListStream):
    """Full-table Braze campaign list (ids and light metadata)."""

    name = "campaigns"
    path = "/campaigns/list"
    records_key = "campaigns"

    schema = th.PropertiesList(
        th.Property("id", th.StringType, required=True),
        th.Property("name", th.StringType),
        th.Property("last_edited", th.DateTimeType),
        th.Property("is_api_campaign", th.BooleanType),
        th.Property("tags", th.ArrayType(th.StringType)),
    ).to_dict()

    def get_child_context(
        self, record: dict[str, Any], context: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Fan each campaign id out to one campaign_details request."""
        return {"campaign_id": record["id"]}


class CanvasesStream(BrazeListStream):
    """Full-table Braze canvas list (ids and light metadata)."""

    name = "canvases"
    path = "/canvas/list"
    records_key = "canvases"

    schema = th.PropertiesList(
        th.Property("id", th.StringType, required=True),
        th.Property("name", th.StringType),
        th.Property("last_edited", th.DateTimeType),
        th.Property("tags", th.ArrayType(th.StringType)),
    ).to_dict()

    def get_child_context(
        self, record: dict[str, Any], context: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Fan each canvas id out to one canvas_details request."""
        return {"canvas_id": record["id"]}


class CampaignDetailsStream(BrazeDetailsStream):
    """Full-table Braze campaign attributes, one call per campaign id."""

    name = "campaign_details"
    path = "/campaigns/details"
    parent_stream_type = CampaignsStream
    primary_keys = ("campaign_id",)
    id_param = "campaign_id"
    id_key = "campaign_id"

    schema = th.PropertiesList(
        th.Property("campaign_id", th.StringType, required=True),
        th.Property("name", th.StringType),
        th.Property("description", th.StringType),
        th.Property("schedule_type", th.StringType),
        th.Property("channels", th.ArrayType(th.StringType)),
        th.Property("created_at", th.DateTimeType),
        th.Property("updated_at", th.DateTimeType),
        th.Property("first_sent", th.DateTimeType),
        th.Property("last_sent", th.DateTimeType),
        th.Property("archived", th.BooleanType),
        th.Property("draft", th.BooleanType),
        th.Property("enabled", th.BooleanType),
        th.Property("has_post_launch_draft", th.BooleanType),
        th.Property("tags", th.ArrayType(th.StringType)),
        th.Property("teams", th.ArrayType(th.StringType)),
        th.Property("messages", th.ObjectType(additional_properties=True)),
        th.Property(
            "conversion_behaviors",
            th.ArrayType(th.ObjectType(additional_properties=True)),
        ),
    ).to_dict()


class CanvasDetailsStream(BrazeDetailsStream):
    """Full-table Braze canvas attributes, one call per canvas id."""

    name = "canvas_details"
    path = "/canvas/details"
    parent_stream_type = CanvasesStream
    primary_keys = ("canvas_id",)
    id_param = "canvas_id"
    id_key = "canvas_id"

    schema = th.PropertiesList(
        th.Property("canvas_id", th.StringType, required=True),
        th.Property("name", th.StringType),
        th.Property("description", th.StringType),
        th.Property("schedule_type", th.StringType),
        th.Property("channels", th.ArrayType(th.StringType)),
        th.Property("created_at", th.DateTimeType),
        th.Property("updated_at", th.DateTimeType),
        th.Property("first_entry", th.DateTimeType),
        th.Property("last_entry", th.DateTimeType),
        th.Property("archived", th.BooleanType),
        th.Property("draft", th.BooleanType),
        th.Property("enabled", th.BooleanType),
        th.Property("has_post_launch_draft", th.BooleanType),
        th.Property("tags", th.ArrayType(th.StringType)),
        th.Property("teams", th.ArrayType(th.StringType)),
        th.Property(
            "variants", th.ArrayType(th.ObjectType(additional_properties=True))
        ),
        th.Property("steps", th.ArrayType(th.ObjectType(additional_properties=True))),
    ).to_dict()


def _retry_after_seconds(exception: Any) -> float:
    """Read the numeric Retry-After header, falling back for other retries."""
    if not isinstance(exception, RetriableAPIError) or exception.response is None:
        return 2.0
    retry_after = exception.response.headers.get("Retry-After")
    if retry_after is None:
        return 2.0
    try:
        return max(0.0, float(retry_after))
    except TypeError, ValueError:
        return 2.0


def _records(response: requests.Response, records_key: str) -> list[Any]:
    """Validate and return the records array from a Braze list envelope."""
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Braze response must be an object")

    records = payload.get(records_key, [])
    if not isinstance(records, list):
        raise ValueError(f"Braze response {records_key} must be a list")
    return records
