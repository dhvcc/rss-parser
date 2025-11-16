from typing import Optional

from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.feed import Feed
from rss_parser.models.types.tag import Tag


class Atom(XMLBaseModel):
    """Atom 1.0"""

    version: Optional[Tag[str]] = Field(alias="@version", default=None)
    feed: Tag[Feed]
