from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.person import Person
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RequiredAtomEntryMixin(XMLBaseModel):
    id: Tag[str]
    "Identifier for the entry."

    title: Tag[str]
    "The title of the entry."

    updated: Tag[DateTimeOrStr]
    "Indicates when the entry was updated."


class RecommendedAtomEntryMixin(XMLBaseModel):
    authors: Optional[OnlyList[Tag[Person]]] = pydantic.Field(alias="author", default=[])
    "Entry authors."

    links: Optional[OnlyList[Tag[str]]] = pydantic.Field(alias="link", default=[])
    "The URL of the entry."

    content: Optional[Tag[str]] = None
    "The main content of the entry."

    summary: Optional[Tag[str]] = None
    "Conveys a short summary, abstract, or excerpt of the entry. Some feeds use this tag as the main content."


class OptionalAtomEntryMixin(XMLBaseModel):
    categories: Optional[OnlyList[Tag[dict]]] = pydantic.Field(alias="category", default=[])
    "Specifies a categories that the entry belongs to."

    contributors: Optional[OnlyList[Tag[Person]]] = pydantic.Field(alias="contributor", default=[])
    "Entry contributors."

    rights: Optional[Tag[str]] = None
    "The copyright of the entry."

    published: Optional[Tag[DateTimeOrStr]] = None
    "Indicates when the entry was published."

    source: Optional[Tag[str]] = None
    "Contains metadata from the source feed if this entry is a copy."


class Entry(RequiredAtomEntryMixin, RecommendedAtomEntryMixin, OptionalAtomEntryMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
