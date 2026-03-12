from datetime import date, datetime

from dateutil import parser as dateutil_parser


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
