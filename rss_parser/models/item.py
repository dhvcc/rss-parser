from typing import Optional

from rss_parser.models import RSSBaseModel
from rss_parser.models.types.tag import Tag


class RequiredItemElementsMixin(RSSBaseModel):
    title: str = None  # Venice Film Festival Tries to Quit Sinking
    "The title of the item."

    link: str = None  # http://nytimes.com/2004/12/07FEST.html
    "The URL of the item."

    description: str = None  # <description>Some of the most heated chatter at the Venice Film Festival this week was
    # about the way that the arrival of the stars at the Palazzo del Cinema was being staged.</description>
    "The item synopsis."


class OptionalItemElementsMixin(RSSBaseModel):
    author: Optional[str] = None
    "Email address of the author of the item."

    # FIXME: uncomment
    # category: Optional[str] = None
    "Includes the item in one or more categories."

    comments: Optional[str] = None
    "URL of a page for comments relating to the item."

    enclosure: Optional[Tag[str]] = None
    "Describes a media object that is attached to the item."

    guid: Optional[Tag[str]] = None
    "A string that uniquely identifies the item."

    pub_date: Optional[str] = None
    "Indicates when the item was published."

    source: Optional[str] = None
    "The RSS channel that the item came from."


class Item(RequiredItemElementsMixin, OptionalItemElementsMixin):
    """https://www.rssboard.org/rss-specification#hrelementsOfLtitemgt."""
