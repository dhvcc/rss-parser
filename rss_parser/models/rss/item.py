from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class RequiredItemElementsMixin(XMLBaseModel):
    title: Tag[str] = None  # Venice Film Festival Tries to Quit Sinking
    "The title of the item."

    link: Tag[str] = None  # http://nytimes.com/2004/12/07FEST.html
    "The URL of the item."

    description: Tag[
        str
    ] = None  # <description>Some of the most heated chatter at the Venice Film Festival this week was
    # about the way that the arrival of the stars at the Palazzo del Cinema was being staged.</description>
    "The item synopsis."


class OptionalItemElementsMixin(XMLBaseModel):
    author: Optional[Tag[str]] = None
    "Email address of the author of the item."

    category: Optional[Tag[str]] = None
    "Includes the item in one or more categories."

    comments: Optional[Tag[str]] = None
    "URL of a page for comments relating to the item."

    enclosure: Optional[Tag[str]] = None
    "Describes a media object that is attached to the item."

    guid: Optional[Tag[str]] = None
    "A string that uniquely identifies the item."

    pub_date: Optional[Tag[str]] = None
    "Indicates when the item was published."

    source: Optional[Tag[str]] = None
    "The RSS channel that the item came from."


class Item(RequiredItemElementsMixin, OptionalItemElementsMixin, XMLBaseModel):
    """https://www.rssboard.org/rss-specification#hrelementsOfLtitemgt."""
