from rss_parser.models import XMLBaseModel
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.tag import Tag


class Source(XMLBaseModel):
    id: Tag[str] | None = None
    "Source id."

    title: Tag[str] | None = None
    "Title of the source."

    updated: Tag[DateTimeOrStr] | None = None
    "When source was updated."
