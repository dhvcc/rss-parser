from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.entry import Entry
from rss_parser.models.image import Image
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RequiredAtomFeedMixin(XMLBaseModel):
    feed_id: Tag[str] = pydantic.Field(alias="id")
    "Identifies the feed using a universally unique and permanent URI."

    title: Tag[str]
    "Contains a human readable title for the feed."

    updated: Tag[DateTimeOrStr]
    "Indicates the last time the feed was modified in a significant way."


class RecommendedAtomFeedMixin(XMLBaseModel):
    author: Optional[Tag[str]] = None
    "Names one author of the feed. A feed may have multiple author elements."

    link: Optional[Tag[list]] = None
    "The URL to the feed. A feed may have multiple link elements."


class OptionalAtomFeedMixin(XMLBaseModel):
    entries: Optional[OnlyList[Tag[Entry]]] = pydantic.Field(alias="entry", default=[])
    "The entries in the feed. A feed may have multiple entry elements."

    category: Optional[Tag[str]] = None
    "Specifies a categories that the feed belongs to. The feed may have multiple categories elements."

    contributor: Optional[Tag[str]] = None
    "Names one contributor to the feed. A feed may have multiple contributor elements."

    generator: Optional[Tag[str]] = None
    "Identifies the software used to generate the feed, for debugging and other purposes."

    icon: Optional[Tag[Image]] = None
    "Identifies a small image which provides iconic visual identification for the feed. Icons should be square."

    logo: Optional[Tag[Image]] = None
    "Identifies a larger image which provides visual identification for the feed.\
    Images should be twice as wide as they are tall."

    rights: Optional[Tag[str]] = None
    "The copyright of the feed."

    subtitle: Optional[Tag[str]] = None
    "Contains a human readable description or subtitle for the feed."


class Feed(RequiredAtomFeedMixin, RecommendedAtomFeedMixin, OptionalAtomFeedMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
