from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.tag import Tag


class Source(XMLBaseModel):
    id: Optional[Tag[str]] = None
    "Source id."

    title: Optional[Tag[str]] = None
    "Title of the source."

    updated: Optional[Tag[DateTimeOrStr]] = None
    "When source was updated."
