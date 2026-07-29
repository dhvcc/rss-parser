from typing import Generic

from pydantic import Field
from typing_extensions import TypeVar

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss.channel import Channel
from rss_parser.models.types.tag import Tag

ChannelT = TypeVar("ChannelT", bound=XMLBaseModel, default=Channel)


class RSS(XMLBaseModel, Generic[ChannelT]):
    """
    RSS 0.9x / 2.0 (https://www.rssboard.org/rss-specification).

    Generic over the channel type: ``RSS[Channel[MyItem]]`` or ``RSS[MyChannel]``.
    """

    version: Tag[str] | None = Field(alias="@version", default=None)
    channel: Tag[ChannelT]
