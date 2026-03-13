from datetime import date, datetime

from dateutil import parser as dateutil_parser

DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"


def get_partition_path_from_schema_and_record(
    schema: dict,
    record: dict,
    fallback_date: datetime,
    *,
    partition_date_format: str = DEFAULT_PARTITION_DATE_FORMAT,
) -> str:
    """Build partition path from stream schema (x-partition-fields) and record.

    When x-partition-fields is missing or empty, returns fallback_date formatted
    with partition_date_format. Otherwise, for each field in order: string values
    are parsed as dates only when the property schema has format "date" or
    "date-time"; native datetime/date are always treated as date segments. When
    format is absent and the value is a string, it is appended as a path-safe
    literal (slashes replaced with underscore). No date inference from string
    content. Segments are joined with /.

    Args:
        schema: Stream schema dict; may contain x-partition-fields list.
        record: Record dict with field values.
        fallback_date: Date used when x-partition-fields is missing or empty.
        partition_date_format: strftime format for date segments (keyword-only).

    Returns:
        Partition path string (e.g. "eu/year=2024/month=03/day=11").

    Raises:
        ParserError: From dateutil when a string is parsed as date and fails.
    """
    partition_fields = schema.get("x-partition-fields")
    if not (isinstance(partition_fields, list) and len(partition_fields) > 0):
        return fallback_date.strftime(partition_date_format)

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
            segments.append(str(value).replace("/", "_"))

    return "/".join(segments)


def get_partition_path_from_record(
    record: dict,
    partition_date_field: str,
    partition_date_format: str,
    fallback_date: datetime,
) -> str:
    """Resolve partition path string from the record's date field.

    Reads the record field named by partition_date_field. String values are parsed
    with dateutil.parser.parse (flexible formats; no tzinfos). Unparseable strings
    raise ParserError; unsupported timezone in the string may produce
    UnknownTimezoneWarning from dateutil. If the field is missing or the value is
    not a string (or is None), returns fallback_date formatted with
    partition_date_format. Callers may use DEFAULT_PARTITION_DATE_FORMAT for
    Hive-style paths.

    Args:
        record: Record dict containing the partition date field.
        partition_date_field: Key in record for the date/datetime value.
        partition_date_format: strftime format for the returned path segment.
        fallback_date: Date used when field is missing or value is non-string/None.

    Returns:
        Partition path string (e.g. "year=2024/month=03/day=11").
    """
    value = record.get(partition_date_field)
    if value is None:
        return fallback_date.strftime(partition_date_format)
    if isinstance(value, (datetime, date)):
        return value.strftime(partition_date_format)
    if not isinstance(value, str):
        return fallback_date.strftime(partition_date_format)
    # Use dateutil for flexible format support; do not pass tzinfos.
    parsed = dateutil_parser.parse(value)
    return str(parsed.strftime(partition_date_format))
