from typing import Any


def is_date_field(field_definition: dict[str, Any]) -> bool:
    field_type = field_definition.get("type")
    if field_type in ["date", "datetime"]:
        return True

    field_format = field_definition.get("format")
    return field_format and field_format in ["date", "date-time"]
