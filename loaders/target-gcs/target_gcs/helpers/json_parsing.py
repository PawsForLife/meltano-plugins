import decimal
from typing import Any


def _json_default(obj: Any) -> float:
    """Used as orjson default to serialize Decimal as float.

    Returns float(obj) when obj is a decimal.Decimal; raises TypeError for any
    other type so non-serializable values are not silently converted.
    """
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON-serializable")
