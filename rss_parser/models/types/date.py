from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Union

from rss_parser.models.types.tag import Tag

DatetimeOrStr = Union[str, datetime]


def validate_dt_or_str(value: Union[str, Tag]) -> DatetimeOrStr:
    if hasattr(value, "content"):
        value = value.content
    # Try to parse standard (RFC 822)
    try:
        return parsedate_to_datetime(value)
    except ValueError:
        pass
    # Try ISO
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    # Try timestamp
    try:
        return datetime.fromtimestamp(int(value))
    except ValueError:
        pass

    return value
