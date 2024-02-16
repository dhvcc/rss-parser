from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.entry import Entry
from rss_parser.models.atom.person import Person
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RequiredAtomFeedMixin(XMLBaseModel):
    id: Tag[str]
    "Identifies the feed using a universally unique and permanent URI."

    title: Tag[str]
    "Contains a human readable title for the feed."

    updated: Tag[DateTimeOrStr]
    "Indicates the last time the feed was modified in a significant way."


class RecommendedAtomFeedMixin(XMLBaseModel):
    authors: Optional[OnlyList[Tag[Person]]] = pydantic.Field(alias="author", default=[])
    "Names one author of the feed. A feed may have multiple author elements."

    links: Optional[OnlyList[Tag[str]]] = pydantic.Field(alias="link", default=[])
    "The URL to the feed. A feed may have multiple link elements."


class OptionalAtomFeedMixin(XMLBaseModel):
    entries: Optional[OnlyList[Tag[Entry]]] = pydantic.Field(alias="entry", default=[])
    "The entries in the feed. A feed may have multiple entry elements."

    categories: Optional[OnlyList[Tag[dict]]] = pydantic.Field(alias="category", default=[])
    "Specifies a categories that the feed belongs to. The feed may have multiple categories elements."

    contributors: Optional[OnlyList[Tag[Person]]] = pydantic.Field(alias="contributor", default=[])
    "Feed contributors."

    generator: Optional[Tag[str]] = None
    "Identifies the software used to generate the feed, for debugging and other purposes."

    icon: Optional[Tag[str]] = None
    "Identifies a small image which provides iconic visual identification for the feed. Icons should be square."

    logo: Optional[Tag[str]] = None
    "Identifies a larger image which provides visual identification for the feed. \
    Images should be twice as wide as they are tall."

    rights: Optional[Tag[str]] = None
    "The copyright of the feed."

    subtitle: Optional[Tag[str]] = None
    "Contains a human readable description or subtitle for the feed."


class Feed(RequiredAtomFeedMixin, RecommendedAtomFeedMixin, OptionalAtomFeedMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
