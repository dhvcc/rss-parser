from typing import Optional

from rss_parser.models.legacy import XMLBaseModel
from rss_parser.models.legacy.pydantic_proxy import import_v1_pydantic
from rss_parser.models.legacy.types.date import DateTimeOrStr
from rss_parser.models.legacy.types.tag import Tag

pydantic = import_v1_pydantic()


class Source(XMLBaseModel):
    id: Optional[Tag[str]] = None
    "Source id."

    title: Optional[Tag[str]] = None
    "Title of the source."

    updated: Optional[Tag[DateTimeOrStr]] = None
    "When source was updated."
