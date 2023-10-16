from datetime import datetime
from email.utils import parsedate_to_datetime

from pydantic.validators import parse_datetime


class DateTimeOrStr(datetime):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v) -> datetime:
        # Try to parse standard (RFC 821)
        try:
            return parsedate_to_datetime(v)
        except ValueError:
            pass
        # Try ISO
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            pass
        # Try timestamp
        try:
            return datetime.fromtimestamp(int(v))
        except ValueError:
            pass

        return parse_datetime(v)

    def __repr__(self):
        return f"DateTimeOrStp({super().__repr__()})"
