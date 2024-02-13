from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RequiredAtomEntryMixin(XMLBaseModel):
    entry_id: Tag[str] = pydantic.Field(alias="id")
    title: Tag[str]
    updated: Tag[str]


class RecommendedAtomEntryMixin(XMLBaseModel):
    author: Optional[Tag[dict]] = None
    link: Optional[Tag[list]] = None
    content: Optional[Tag[dict]] = None
    summary: Optional[Tag[str]] = None


class OptionalAtomEntryMixin(XMLBaseModel):
    category: Optional[Tag[dict]] = None
    contributor: Optional[Tag[dict]] = None
    rights: Optional[Tag[str]] = None
    published: Optional[Tag[DateTimeOrStr]] = None
    source: Optional[Tag[str]] = None


class Entry(RequiredAtomEntryMixin, RecommendedAtomEntryMixin, OptionalAtomEntryMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
