from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RequiredAtomEntryMixin(XMLBaseModel):
    entry_id: Tag[str] = pydantic.Field(alias="id")
    "Identifier for the entry."

    title: Tag[str]
    "The title of the entry."

    updated: Tag[str]
    "Indicates when the entry was updated."


class RecommendedAtomEntryMixin(XMLBaseModel):
    author: Optional[Tag[dict]] = None
    "Email, name, and URI of the author of the entry."

    link: Optional[Tag[list]] = None
    "The URL of the entry."

    content: Optional[Tag[dict]] = None
    "The main content of the entry."

    summary: Optional[Tag[str]] = None
    "Conveys a short summary, abstract, or excerpt of the entry. Some feeds use this tag as the main content."


class OptionalAtomEntryMixin(XMLBaseModel):
    category: Optional[Tag[dict]] = None
    "Specifies a categories that the feed belongs to."

    contributor: Optional[Tag[dict]] = None
    "Email, name, and URI of the contributors of the entry."

    rights: Optional[Tag[str]] = None
    "The copyright of the entry."

    published: Optional[Tag[DateTimeOrStr]] = None
    "Indicates when the entry was published."

    source: Optional[Tag[str]] = None
    "Contains metadata from the source feed if this entry is a copy."


class Entry(RequiredAtomEntryMixin, RecommendedAtomEntryMixin, OptionalAtomEntryMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
