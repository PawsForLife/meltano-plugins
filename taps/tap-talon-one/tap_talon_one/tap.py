"""Talon.One tap entry point."""

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_talon_one.streams import CampaignsStream


class TalonOneTap(Tap):
    """Extract data from the Talon.One Management API."""

    name = "tap-talon-one"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType(pattern=r"^https?://"),
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
    ).to_dict()

    def discover_streams(self) -> list[CampaignsStream]:
        """Return the streams exposed by this tap."""
        return [CampaignsStream(self)]


if __name__ == "__main__":
    TalonOneTap.cli()
