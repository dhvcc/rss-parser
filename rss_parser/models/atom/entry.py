from typing import Optional

from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.person import Person
from rss_parser.models.atom.source import Source
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.models.types.text_construct import TextConstruct


class Entry(XMLBaseModel):
    """https://validator.w3.org/feed/docs/atom.html#requiredEntryElements"""

    # Required entry elements

    id: Tag[str]
    "Identifier for the entry."

    title: Tag[TextConstruct]
    "The title of the entry."

    updated: Optional[Tag[DateTimeOrStr]] = None
    "Indicates when the entry was updated. Required by the spec, but omitted often enough in the wild that it's optional here."  # noqa: E501

    # Recommended entry elements

    authors: OnlyList[Tag[Person]] = Field(alias="author", default_factory=OnlyList)
    "Entry authors."

    links: OnlyList[Tag[str]] = Field(alias="link", default_factory=OnlyList)
    "The URL of the entry."

    content: Optional[Tag[TextConstruct]] = None
    "The main content of the entry."

    summary: Optional[Tag[TextConstruct]] = None
    "Conveys a short summary, abstract, or excerpt of the entry. Some feeds use this tag as the main content."

    # Optional entry elements

    categories: OnlyList[Tag[dict]] = Field(alias="category", default_factory=OnlyList)
    "Specifies a categories that the entry belongs to."

    contributors: OnlyList[Tag[Person]] = Field(alias="contributor", default_factory=OnlyList)
    "Entry contributors."

    rights: Optional[Tag[TextConstruct]] = None
    "The copyright of the entry."

    published: Optional[Tag[DateTimeOrStr]] = None
    "Indicates when the entry was published."

    source: Optional[Tag[Source]] = None
    "Contains metadata from the source feed if this entry is a copy."
