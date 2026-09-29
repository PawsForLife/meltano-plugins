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
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import requests
from singer_sdk import typing as th
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.pagination import PageNumberPaginator, SinglePagePaginator
from singer_sdk.streams import RESTStream

from tap_braze.models import (
    CampaignDetailResponse,
    CampaignListResponse,
    CanvasDetailResponse,
    CanvasListResponse,
)


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

    Subclasses set ``name``, ``path``, ``records_key`` (the model field holding
    the list rows), ``list_model`` (the envelope model validated on each page),
    and ``schema``.
    """

    primary_keys = ("id",)
    replication_method = "FULL_TABLE"
    records_key: str
    list_model: type[CampaignListResponse | CanvasListResponse]
    # Braze list endpoints omit archived campaigns/canvases unless asked. This
    # tap replicates the full descriptive catalogue, so it opts archived rows
    # in; every parent id must reach its details call.
    include_archived = True

    def get_new_paginator(self) -> PageNumberPaginator:
        """Page through the 0-indexed list until an empty page.

        Braze sends no next-page flag, so pagination relies on the SDK halting
        once :meth:`parse_response` yields no records for a page.
        """
        return PageNumberPaginator(start_value=0)

    def get_url_params(
        self,
        context: Mapping[str, Any] | None,
        next_page_token: int | None,
    ) -> dict[str, Any]:
        """Request the current 0-indexed page, including archived records."""
        params: dict[str, Any] = {"page": next_page_token or 0}
        if self.include_archived:
            params["include_archived"] = "true"
        return params

    def parse_response(self, response: requests.Response) -> Iterable[dict[str, Any]]:
        """Validate the list envelope into its model, then yield its records.

        Loading the response into ``list_model`` requires the records key and
        rejects a non-object row, so a malformed or key-less response is
        rejected here rather than mistaken for an empty final page.
        """
        envelope = self.list_model.model_validate_json(response.content)
        records: list[dict[str, Any]] = getattr(envelope, self.records_key)
        yield from records


class BrazeDetailsStream(BrazeStream):
    """Base full-table Braze details child stream.

    One request per parent id. The details payload does not echo the id, so it
    is injected from the parent context and used as the primary key. Subclasses
    set ``name``, ``path``, ``parent_stream_type``, ``id_param`` (the query
    parameter naming the id), ``id_key`` (the injected context/record key),
    ``detail_model`` (the payload model validated on each call), and ``schema``.
    """

    replication_method = "FULL_TABLE"
    id_param: str
    id_key: str
    detail_model: type[CampaignDetailResponse | CanvasDetailResponse]

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
        """Validate the details payload into its model, then yield the record.

        Loading the response into ``detail_model`` rejects a malformed payload
        before it can reach ``post_process`` or the emitted record; the model
        drops the API status envelope and keeps only the attributes it set.
        """
        detail = self.detail_model.model_validate_json(response.content)
        yield detail.to_record()

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
    list_model = CampaignListResponse

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
    list_model = CanvasListResponse

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
    detail_model = CampaignDetailResponse

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
    detail_model = CanvasDetailResponse

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


_DEFAULT_RETRY_WAIT = 2.0


def _retry_after_seconds(exception: Any) -> float:
    """Return the Retry-After wait for a rate-limited request.

    Falls back to a short default when the exception carries no usable
    Retry-After header.
    """
    if not isinstance(exception, RetriableAPIError) or exception.response is None:
        return _DEFAULT_RETRY_WAIT
    retry_after = exception.response.headers.get("Retry-After")
    if retry_after is None:
        return _DEFAULT_RETRY_WAIT
    return _parse_retry_after(retry_after)


def _parse_retry_after(retry_after: str) -> float:
    """Parse a Retry-After value into seconds to wait.

    RFC 9110 allows either delta-seconds or an HTTP-date; parse both, and use
    the default only when neither yields a usable wait.
    """
    value = retry_after.strip()
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        pass
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return _DEFAULT_RETRY_WAIT
    if retry_at is None:
        return _DEFAULT_RETRY_WAIT
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=UTC)
    delay = (retry_at - datetime.now(UTC)).total_seconds()
    return max(0.0, delay)
