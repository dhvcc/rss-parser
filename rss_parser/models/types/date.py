from email.utils import parsedate_to_datetime
from datetime import datetime
from typing import Union

DatetimeOrStr = Union[str, datetime]


def validate_dt_or_str(value: str) -> DatetimeOrStr:
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
