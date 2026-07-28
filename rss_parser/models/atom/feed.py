from typing import Generic, Optional

from pydantic import Field
from typing_extensions import TypeVar

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.entry import Entry
from rss_parser.models.atom.person import Person
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.models.types.text_construct import TextConstruct

EntryT = TypeVar("EntryT", bound=XMLBaseModel, default=Entry)


class Feed(XMLBaseModel, Generic[EntryT]):
    """
    https://validator.w3.org/feed/docs/atom.html

    Generic over the entry type, so a custom entry schema is one parametrization away:
    ``Feed[MyEntry]``.
    """

    # Required feed elements

    id: Tag[str]
    "Identifies the feed using a universally unique and permanent URI."

    title: Tag[TextConstruct]
    "Contains a human readable title for the feed."

    updated: Optional[Tag[DateTimeOrStr]] = None
    "Indicates the last time the feed was modified in a significant way. Required by the spec, but omitted by major real-world publishers (e.g. YouTube), so it's optional here."  # noqa: E501

    # Recommended feed elements

    authors: OnlyList[Tag[Person]] = Field(alias="author", default_factory=OnlyList)
    "Names one author of the feed. A feed may have multiple author elements."

    links: OnlyList[Tag[str]] = Field(alias="link", default_factory=OnlyList)
    "The URL to the feed. A feed may have multiple link elements."

    # Optional feed elements

    entries: OnlyList[Tag[EntryT]] = Field(alias="entry", default_factory=OnlyList)
    "The entries in the feed. A feed may have multiple entry elements."

    categories: OnlyList[Tag[dict]] = Field(alias="category", default_factory=OnlyList)
    "Specifies a categories that the feed belongs to. The feed may have multiple categories elements."

    contributors: OnlyList[Tag[Person]] = Field(alias="contributor", default_factory=OnlyList)
    "Feed contributors."

    generator: Optional[Tag[str]] = None
    "Identifies the software used to generate the feed, for debugging and other purposes."

    icon: Optional[Tag[str]] = None
    "Identifies a small image which provides iconic visual identification for the feed. Icons should be square."

    logo: Optional[Tag[str]] = None
    "Identifies a larger image which provides visual identification for the feed. \
    Images should be twice as wide as they are tall."

    rights: Optional[Tag[TextConstruct]] = None
    "The copyright of the feed."

    subtitle: Optional[Tag[TextConstruct]] = None
    "Contains a human readable description or subtitle for the feed."
