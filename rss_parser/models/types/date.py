from datetime import datetime
from email.utils import parsedate_to_datetime

from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic_validators = import_v1_pydantic(".validators")


class DateTimeOrStr(datetime):
    @classmethod
    def __get_validators__(cls):
        yield validate_dt_or_str

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(
            examples=[datetime(1970, 1, 1, 0, 0, 0)],
        )

    @classmethod
    def validate(cls, v):
        return validate_dt_or_str(v)

    def __repr__(self):
        return f"DateTimeOrStp({super().__repr__()})"


def validate_dt_or_str(value: str) -> datetime:
    # Try to parse standard (RFC 822)
    try:
        return parsedate_to_datetime(value)
    except (ValueError, TypeError):  # https://github.com/python/cpython/issues/74866
        pass
    # Try ISO or timestamp
    try:
        return pydantic_validators.parse_datetime(value)
    except ValueError:
        pass

    return value
