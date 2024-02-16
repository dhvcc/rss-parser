from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss.channel import Channel
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RSS(XMLBaseModel):
    """RSS 2.0."""

    version: Optional[Tag[str]] = pydantic.Field(alias="@version")
    channel: Tag[Channel]
