from typing import Optional

from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.person import Person
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag


class RequiredAtomEntryMixin(XMLBaseModel):
    id: Tag[str]
    "Identifier for the entry."

    title: Tag[str]
    "The title of the entry."

    updated: Tag[DateTimeOrStr]
    "Indicates when the entry was updated."


class RecommendedAtomEntryMixin(XMLBaseModel):
    authors: OnlyList[Tag[Person]] = Field(alias="author", default_factory=OnlyList)
    "Entry authors."

    links: OnlyList[Tag[str]] = Field(alias="link", default_factory=OnlyList)
    "The URL of the entry."

    content: Optional[Tag[str]] = None
    "The main content of the entry."

    summary: Optional[Tag[str]] = None
    "Conveys a short summary, abstract, or excerpt of the entry. Some feeds use this tag as the main content."


class OptionalAtomEntryMixin(XMLBaseModel):
    categories: OnlyList[Tag[dict]] = Field(alias="category", default_factory=OnlyList)
    "Specifies a categories that the entry belongs to."

    contributors: OnlyList[Tag[Person]] = Field(alias="contributor", default_factory=OnlyList)
    "Entry contributors."

    rights: Optional[Tag[str]] = None
    "The copyright of the entry."

    published: Optional[Tag[DateTimeOrStr]] = None
    "Indicates when the entry was published."

    source: Optional[Tag[str]] = None
    "Contains metadata from the source feed if this entry is a copy."


class Entry(RequiredAtomEntryMixin, RecommendedAtomEntryMixin, OptionalAtomEntryMixin, XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html"""
