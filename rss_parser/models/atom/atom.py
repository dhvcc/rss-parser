from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.feed import Feed
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class Atom(XMLBaseModel):
    """Atom 1.0"""

    version: Optional[Tag[str]] = pydantic.Field(alias="@version")
    feed: Tag[Feed]
