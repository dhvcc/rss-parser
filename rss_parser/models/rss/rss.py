from typing import Optional

from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss.channel import Channel
from rss_parser.models.types.tag import Tag


class RSS(XMLBaseModel):
    """RSS 2.0."""

    version: Optional[Tag[str]] = Field(alias="@version", default=None)
    channel: Tag[Channel]
