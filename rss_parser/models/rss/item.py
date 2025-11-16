from typing import Optional

from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag


class RequiredItemElementsMixin(XMLBaseModel):
    title: Tag[str]  # Venice Film Festival Tries to Quit Sinking
    "The title of the item."

    links: OnlyList[Tag[str]] = Field(alias="link")  # http://nytimes.com/2004/12/07FEST.html
    "The URL of the item."

    description: Tag[str]  # <description>Some of the most heated chatter at the Venice Film Festival this week was
    # about the way that the arrival of the stars at the Palazzo del Cinema was being staged.</description>
    "The item synopsis."


class OptionalItemElementsMixin(XMLBaseModel):
    author: Optional[Tag[str]] = None
    "Email address of the author of the item."

    categories: OnlyList[Tag[str]] = Field(alias="category", default_factory=OnlyList)
    "Includes the item in one or more categories."

    comments: Optional[Tag[str]] = None
    "URL of a page for comments relating to the item."

    enclosures: OnlyList[Tag[str]] = Field(alias="enclosure", default_factory=OnlyList)
    # enclosure: Optional[OnlyList[Tag[str]]] = None
    "Describes a media object that is attached to the item.\nCan be a list -> https://validator.w3.org/feed/docs/warning/DuplicateEnclosure.html"

    guid: Optional[Tag[str]] = None
    "A string that uniquely identifies the item."

    pub_date: Optional[Tag[str]] = None
    "Indicates when the item was published."

    source: Optional[Tag[str]] = None
    "The RSS channel that the item came from."


class Item(RequiredItemElementsMixin, OptionalItemElementsMixin, XMLBaseModel):
    """https://www.rssboard.org/rss-specification#hrelementsOfLtitemgt."""
