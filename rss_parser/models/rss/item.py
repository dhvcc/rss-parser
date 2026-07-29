from pydantic import Field, model_validator

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag


class Item(XMLBaseModel):
    """
    https://www.rssboard.org/rss-specification#hrelementsOfLtitemgt

    All elements of an item are optional, however at least one of title or description
    must be present - this is enforced with a validator.
    """

    title: Tag[str] | None = None  # Venice Film Festival Tries to Quit Sinking
    "The title of the item."

    links: OnlyList[Tag[str]] = Field(alias="link", default_factory=OnlyList)  # http://nytimes.com/2004/12/07FEST.html
    "The URL of the item. Can appear multiple times in the wild, so it's always a list."

    description: Tag[str] | None = None
    "The item synopsis."

    author: Tag[str] | None = None
    "Email address of the author of the item."

    categories: OnlyList[Tag[str]] = Field(alias="category", default_factory=OnlyList)
    "Includes the item in one or more categories."

    comments: Tag[str] | None = None
    "URL of a page for comments relating to the item."

    enclosures: OnlyList[Tag[str]] = Field(alias="enclosure", default_factory=OnlyList)
    "Describes a media object that is attached to the item. The url/length/type live in `.attributes`.\nCan be a list -> https://validator.w3.org/feed/docs/warning/DuplicateEnclosure.html"  # noqa: E501

    guid: Tag[str] | None = None
    "A string that uniquely identifies the item."

    pub_date: Tag[DateTimeOrStr] | None = None  # Sat, 07 Sep 2002 00:00:01 GMT
    "Indicates when the item was published."

    source: Tag[str] | None = None
    "The RSS channel that the item came from. The url of the channel lives in `.attributes`."

    @model_validator(mode="after")
    def check_title_or_description(self):
        if self.title is None and self.description is None:
            raise ValueError("either <title> or <description> must be present in an <item>")
        return self
