from typing import Optional

from rss_parser.models.legacy import XMLBaseModel
from rss_parser.models.legacy.atom.feed import Feed
from rss_parser.models.legacy.pydantic_proxy import import_v1_pydantic
from rss_parser.models.legacy.types.tag import Tag

pydantic = import_v1_pydantic()


class Atom(XMLBaseModel):
    """Atom 1.0"""

    version: Optional[Tag[str]] = pydantic.Field(alias="@version")
    feed: Tag[Feed]
