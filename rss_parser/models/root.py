from typing import Optional

from pydantic import Field

from rss_parser.models import RSSBaseModel
from rss_parser.models.channel import Channel
from rss_parser.models.types.tag import Tag


class RSSFeed(RSSBaseModel):
    version: Optional[Tag[str]] = Field(alias="@version")
    channel: Tag[Channel]
