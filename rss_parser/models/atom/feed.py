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
    title: Tag[str]
    updated: Tag[DateTimeOrStr]


class RecommendedAtomFeedMixin(XMLBaseModel):
    author: Optional[Tag[str]] = None
    link: Optional[Tag[list]] = None


class OptionalAtomFeedMixin(XMLBaseModel):
    entries: Optional[OnlyList[Tag[Entry]]] = pydantic.Field(alias="entry", default=[])
    category: Optional[Tag[str]] = None
    contributor: Optional[Tag[str]] = None
    generator: Optional[Tag[str]] = None
    icon: Optional[Tag[Image]] = None
    logo: Optional[Tag[Image]] = None
    rights: Optional[Tag[str]] = None
    subtitle: Optional[Tag[str]] = None


class Feed(RequiredAtomFeedMixin, RecommendedAtomFeedMixin, OptionalAtomFeedMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
