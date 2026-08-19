from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Union

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter, ValidationError
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

datetime_adapter = TypeAdapter(datetime)


class DateTimeOrStr(datetime):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "examples": ["1970-01-01T00:00:00"],
        }

    @classmethod
    def validate(cls, value: Any) -> Union[datetime, str]:
        return validate_dt_or_str(value)

    def __repr__(self) -> str:
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
