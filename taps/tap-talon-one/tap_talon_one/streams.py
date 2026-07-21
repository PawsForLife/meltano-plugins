"""Talon.One Management API streams."""

from __future__ import annotations

from collections.abc import Generator, Iterable, Mapping
from datetime import datetime, timedelta
from typing import Any, NotRequired, TypedDict, cast

import requests
from singer_sdk import typing as th
from singer_sdk.exceptions import RetriableAPIError
from singer_sdk.pagination import OffsetPaginator
from singer_sdk.streams import RESTStream


class TalonOnePage(TypedDict):
    """Validated Talon.One list response envelope."""

    data: list[dict[str, Any]]
    hasMore: NotRequired[bool]
    totalResultSize: NotRequired[int]


class TalonOnePaginator(OffsetPaginator):
    """Advance Talon.One pageSize/skip pagination."""

    def has_more(self, response: requests.Response) -> bool:
        """Stop on hasMore false, the reported total, or an empty page."""
        page = _validated_page(response)
        if page.get("hasMore") is False or not page["data"]:
            return False

        total = page.get("totalResultSize")
        return total is None or self.current_value + len(page["data"]) < total


class TalonOneStream(RESTStream):
    """Base stream for the Talon.One Management API."""

    @property
    def url_base(self) -> str:
        """Return the configured Talon.One tenant URL."""
        return str(self.config["api_url"]).rstrip("/")

    @property
    def http_headers(self) -> dict[str, str]:
        """Authenticate with the configured Management API key."""
        return {
            "Authorization": f"ManagementKey-v1 {self.config['management_key']}",
        }

    def get_new_paginator(self) -> TalonOnePaginator:
        """Return a fresh offset paginator for each sync."""
        return TalonOnePaginator(start_value=0, page_size=self.config["page_size"])

    def get_url_params(
        self,
        context: Mapping[str, Any] | None,
        next_page_token: int | None,
    ) -> dict[str, Any]:
        """Keep stable sort and paging parameters on every request."""
        return {
            "pageSize": self.config["page_size"],
            "skip": next_page_token or 0,
            "sort": "id",
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict[str, Any]]:
        """Yield records from a validated Talon.One response envelope."""
        yield from _validated_page(response)["data"]

    def backoff_wait_generator(self) -> Generator[float, None, None]:
        """Use Retry-After when Talon.One rate-limits a request."""
        return self.backoff_runtime(value=_retry_after_seconds)

    def backoff_jitter(self, value: float) -> float:
        """Preserve the server-requested Retry-After duration exactly."""
        return value


class CampaignsStream(TalonOneStream):
    """Full-refresh Talon.One campaigns."""

    name = "campaigns"
    primary_keys = ("id",)
    replication_method = "FULL_TABLE"

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, required=True),
        th.Property("applicationId", th.IntegerType),
        th.Property("userId", th.IntegerType),
        th.Property("name", th.StringType),
        th.Property("description", th.StringType),
        th.Property("type", th.StringType),
        th.Property("state", th.StringType),
        th.Property("frontendState", th.StringType),
        th.Property("activeRulesetId", th.IntegerType),
        th.Property("created", th.DateTimeType),
        th.Property("updated", th.DateTimeType),
        th.Property("updatedBy", th.StringType),
        th.Property("startTime", th.DateTimeType),
        th.Property("endTime", th.DateTimeType),
        th.Property("contextId", th.StringType),
        th.Property("features", th.ArrayType(th.StringType)),
        th.Property("linkedStoreIds", th.ArrayType(th.IntegerType)),
        th.Property("valueMapsIds", th.ArrayType(th.IntegerType)),
        th.Property("tags", th.ArrayType(th.StringType)),
        th.Property("budgets", th.ArrayType(th.CustomType({}))),
        th.Property("campaignGroups", th.ArrayType(th.CustomType({}))),
        th.Property("limits", th.ArrayType(th.CustomType({}))),
        th.Property("reevaluateOnReturn", th.BooleanType),
        th.Property("storesImported", th.BooleanType),
        th.Property("attributes", th.ObjectType(additional_properties=True)),
        th.Property("couponSettings", th.ObjectType(additional_properties=True)),
        th.Property("referralSettings", th.ObjectType(additional_properties=True)),
    ).to_dict()

    def __init__(self, tap: Any) -> None:
        """Set the Application-scoped campaigns endpoint."""
        super().__init__(tap)
        self.path = f"/v1/applications/{self.config['application_id']}/campaigns"


class EventsStream(TalonOneStream):
    """Incremental Talon.One application events."""

    name = "events"
    primary_keys = ("id",)
    replication_key = "created"
    is_sorted = True

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, required=True),
        th.Property("created", th.DateTimeType, required=True),
        th.Property("applicationId", th.IntegerType),
        th.Property("sessionId", th.IntegerType),
        th.Property("profileId", th.IntegerType),
        th.Property("type", th.StringType),
        th.Property("attributes", th.ObjectType(additional_properties=True)),
        th.Property("effects", th.ArrayType(th.CustomType({}))),
        th.Property("ruleFailureReasons", th.ArrayType(th.CustomType({}))),
    ).to_dict()

    def __init__(self, tap: Any) -> None:
        """Set the Application-scoped events endpoint."""
        super().__init__(tap)
        self.path = f"/v1/applications/{self.config['application_id']}/events/no_total"
        self._created_after: str | None = None

    def get_url_params(
        self,
        context: Mapping[str, Any] | None,
        next_page_token: int | None,
    ) -> dict[str, Any]:
        """Keep the initial extraction boundary stable across every page."""
        if self._created_after is None:
            state = self.get_context_state(context)
            bookmark = (
                state.get("replication_key_value")
                if state.get("replication_key") == self.replication_key
                else None
            )
            starting_timestamp = (
                datetime.fromisoformat(str(bookmark))
                if bookmark is not None
                else self.get_starting_timestamp(context)
            )
            if starting_timestamp is None:
                raise ValueError("Events require start_date or a Singer bookmark")
            if bookmark is not None:
                starting_timestamp -= timedelta(minutes=self.config["lookback_minutes"])
            self._created_after = starting_timestamp.isoformat()

        return {
            "createdAfter": self._created_after,
            "pageSize": self.config["page_size"],
            "skip": next_page_token or 0,
            "sort": "created",
        }


def _retry_after_seconds(exception: Any) -> float:
    """Read the numeric Retry-After header, falling back for other retries."""
    if not isinstance(exception, RetriableAPIError) or exception.response is None:
        return 2.0
    retry_after = exception.response.headers.get("Retry-After")
    if retry_after is None:
        return 2.0
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return 2.0


def _validated_page(response: requests.Response) -> TalonOnePage:
    """Validate a Talon.One list response before using it."""
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Talon.One response must be an object")

    records = payload.get("data")
    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        raise ValueError("Talon.One response data must be a list of objects")

    has_more = payload.get("hasMore")
    if "hasMore" in payload and not isinstance(has_more, bool):
        raise ValueError("Talon.One response hasMore must be a boolean")

    total = payload.get("totalResultSize")
    if "totalResultSize" in payload and (
        not isinstance(total, int) or isinstance(total, bool)
    ):
        raise ValueError("Talon.One response totalResultSize must be an integer")

    return cast(TalonOnePage, payload)
