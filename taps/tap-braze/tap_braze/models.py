"""Pydantic models for the Braze REST payloads the tap ingests.

Every Braze response is loaded into one of these models before use. A payload
that fails validation is rejected (the ``ValidationError`` propagates and stops
the sync) rather than partially ingested, and once a payload validates it is
never re-checked: the list paginator reuses the records this parse produced.

The list envelopes require their records key and reject non-object members, so
a response missing ``campaigns``/``canvases`` (or carrying a ``null`` row) can
no longer masquerade as an empty final page. The detail models validate the
descriptive attributes while allowing unknown fields through untouched, so a
malformed value cannot reach the emitted Singer record.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class BrazeListRow(BaseModel):
    """One Braze list row: a required string ``id`` plus its other attributes.

    ``id`` is the primary key and the parent context each details call fans out
    from, so a row missing it (or carrying a null/non-string ``id``) is rejected
    at validation rather than failing later in ``get_child_context``. Unknown
    attributes pass through unchanged.
    """

    model_config = ConfigDict(extra="allow")

    id: str


class CampaignListResponse(BaseModel):
    """The ``/campaigns/list`` envelope: a required array of campaign rows."""

    model_config = ConfigDict(extra="allow")

    campaigns: list[BrazeListRow]


class CanvasListResponse(BaseModel):
    """The ``/canvas/list`` envelope: a required array of canvas rows."""

    model_config = ConfigDict(extra="allow")

    canvases: list[BrazeListRow]


class _DetailResponse(BaseModel):
    """Base for a Braze details payload.

    Known attributes are validated; unknown attributes pass through unchanged
    (``extra="allow"``). ``to_record`` drops the API status envelope and any
    attribute the payload did not set, so the emitted record mirrors the
    response rather than inventing null columns.
    """

    model_config = ConfigDict(extra="allow")

    message: str | None = None

    def to_record(self) -> dict[str, Any]:
        """Return the validated attributes as an emittable record."""
        record = self.model_dump(mode="json", exclude_unset=True)
        record.pop("message", None)
        return record


class CampaignDetailResponse(_DetailResponse):
    """The ``/campaigns/details`` payload for one campaign."""

    name: str | None = None
    description: str | None = None
    schedule_type: str | None = None
    channels: list[str] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    first_sent: str | None = None
    last_sent: str | None = None
    archived: bool | None = None
    draft: bool | None = None
    enabled: bool | None = None
    has_post_launch_draft: bool | None = None
    tags: list[str] | None = None
    teams: list[str] | None = None
    messages: dict[str, Any] | None = None
    conversion_behaviors: list[dict[str, Any]] | None = None


class CanvasDetailResponse(_DetailResponse):
    """The ``/canvas/details`` payload for one canvas."""

    name: str | None = None
    description: str | None = None
    schedule_type: str | None = None
    channels: list[str] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    first_entry: str | None = None
    last_entry: str | None = None
    archived: bool | None = None
    draft: bool | None = None
    enabled: bool | None = None
    has_post_launch_draft: bool | None = None
    tags: list[str] | None = None
    teams: list[str] | None = None
    variants: list[dict[str, Any]] | None = None
    steps: list[dict[str, Any]] | None = None
