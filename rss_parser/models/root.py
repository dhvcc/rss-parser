from typing import Optional

from pydantic import Field

from rss_parser.models import RSSBaseModel
from rss_parser.models.channel import Channel


class RSSFeed(RSSBaseModel):
    version: Optional[str] = Field(alias="@version")
    channel: Channel


class RSS(RSSBaseModel):
    rss: RSSFeed
