from datetime import date, datetime

from dateutil import parser as dateutil_parser

DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"


def get_partition_path_from_schema_and_record(
    schema: dict,
    record: dict,
    extraction_date: datetime,
    *,
    partition_date_format: str = DEFAULT_PARTITION_DATE_FORMAT,
) -> str:
    """Build partition path from stream schema (x-partition-fields) and record.

    When x-partition-fields is missing or empty, returns extraction_date formatted
    with partition_date_format (e.g. run/extraction date). Otherwise, for each
    field in order: string values are parsed as dates only when the property
    schema has format "date" or "date-time"; native datetime/date are always
    treated as date segments. When format is absent and the value is a string,
    it is appended as a path-safe literal in Hive standard form: literal
    segments are emitted as field_name=value (slashes in value replaced with
    underscore). No date inference from string content. Segments are joined with /.

    Args:
        schema: Stream schema dict; may contain x-partition-fields list.
        record: Record dict with field values.
        extraction_date: Date used when x-partition-fields is missing or empty
            (e.g. run/extraction date).
        partition_date_format: strftime format for date segments (keyword-only).

    Returns:
        Partition path string (e.g. "region=eu/year=2024/month=03/day=11").

    Raises:
        ParserError: From dateutil when a string is parsed as date and fails.
    """
    partition_fields = schema.get("x-partition-fields")
    if not (isinstance(partition_fields, list) and len(partition_fields) > 0):
        return extraction_date.strftime(partition_date_format)

    properties = schema.get("properties") or {}
    segments: list[str] = []

    for field in partition_fields:
        value = record.get(field)
        prop_schema = properties.get(field) or {}
        fmt = prop_schema.get("format") if isinstance(prop_schema, dict) else None

        is_date = False
        date_value: datetime | date | None = None

        if fmt in ("date", "date-time"):
            is_date = True
            if isinstance(value, (datetime, date)):
                date_value = value
            elif isinstance(value, str):
                date_value = dateutil_parser.parse(value)
        elif isinstance(value, (datetime, date)):
            is_date = True
            date_value = value

        if is_date and date_value is not None:
            segments.append(date_value.strftime(partition_date_format))
        else:
            segments.append(f"{field}={str(value).replace('/', '_')}")

    return "/".join(segments)
