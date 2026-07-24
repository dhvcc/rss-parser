from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag


class SkipHours(XMLBaseModel):
    """https://www.rssboard.org/skip-hours-days#skiphours."""

    hours: OnlyList[Tag[int]] = Field(alias="hour", default_factory=OnlyList)
    "Up to 24 <hour> values between 0 and 23, representing hours in GMT when aggregators may skip the channel."


class SkipDays(XMLBaseModel):
    """https://www.rssboard.org/skip-hours-days#skipdays."""

    days: OnlyList[Tag[str]] = Field(alias="day", default_factory=OnlyList)
    "Up to seven <day> values (Monday..Sunday) when aggregators may skip the channel."
