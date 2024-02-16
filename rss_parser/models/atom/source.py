from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class Source(XMLBaseModel):
    id: Optional[Tag[str]] = None
    "Source id."

    title: Optional[Tag[str]] = None
    "Title of the source."

    updated: Optional[Tag[DateTimeOrStr]] = None
    "When source was updated."
