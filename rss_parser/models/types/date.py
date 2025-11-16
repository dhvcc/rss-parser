from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Union

from pydantic import GetCoreSchemaHandler, TypeAdapter, ValidationError
from pydantic_core import core_schema

datetime_adapter = TypeAdapter(datetime)


class DateTimeOrStr(datetime):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(
            examples=[datetime(1970, 1, 1, 0, 0, 0)],
        )

    @classmethod
    def validate(cls, value):
        return validate_dt_or_str(value)

    def __repr__(self):
        return f"DateTimeOrStr({super().__repr__()})"


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
