from datetime import datetime
from email.utils import parsedate_to_datetime


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
