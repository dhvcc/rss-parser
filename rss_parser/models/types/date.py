from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Annotated, Union

from pydantic import PlainValidator, TypeAdapter, ValidationError, WithJsonSchema

datetime_adapter = TypeAdapter(datetime)


def validate_dt_or_str(value: Union[str, datetime], _info=None):
    if isinstance(value, datetime):
        return value
    # Try to parse standard (RFC 822)
    try:
        return parsedate_to_datetime(value)
    except (ValueError, TypeError):  # https://github.com/python/cpython/issues/74866
        pass
    # Try ISO or timestamp
    try:
        return datetime_adapter.validate_python(value)
    except ValidationError:
        pass

    return value


DateTimeOrStr = Annotated[
    Union[datetime, str],
    PlainValidator(validate_dt_or_str),
    WithJsonSchema({"type": "string", "format": "date-time", "examples": ["1970-01-01T00:00:00"]}),
]
