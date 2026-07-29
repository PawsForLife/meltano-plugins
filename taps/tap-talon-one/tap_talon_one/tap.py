"""Talon.One tap entry point."""

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_talon_one.streams import (
    ApplicationStream,
    CampaignsStream,
    CartItemFiltersStream,
    EventsStream,
    EventTypesStream,
    TalonOneStream,
)


class TalonOneTap(Tap):
    """Extract data from the Talon.One Management API."""

    name = "tap-talon-one"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType(pattern=r"^https://"),
            required=True,
        ),
        th.Property(
            "management_key",
            th.StringType(min_length=1),
            required=True,
            secret=True,
        ),
        th.Property(
            "application_id",
            th.IntegerType(minimum=1),
            required=True,
        ),
        th.Property(
            "page_size",
            th.IntegerType(minimum=1, maximum=1000),
            default=1000,
        ),
        th.Property(
            "start_date",
            th.DateTimeType(
                pattern=(
                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
                    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
                )
            ),
        ),
        th.Property(
            "lookback_minutes",
            th.IntegerType(minimum=0),
            default=5,
        ),
    ).to_dict()

    def discover_streams(self) -> list[TalonOneStream]:
        """Return the streams exposed by this tap."""
        return [
            ApplicationStream(self),
            CampaignsStream(self),
            CartItemFiltersStream(self),
            EventsStream(self),
            EventTypesStream(self),
        ]


if __name__ == "__main__":
    TalonOneTap.cli()
