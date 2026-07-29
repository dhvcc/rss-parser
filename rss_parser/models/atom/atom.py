from typing import Generic

from pydantic import Field
from typing_extensions import TypeVar

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.feed import Feed
from rss_parser.models.types.tag import Tag

FeedT = TypeVar("FeedT", bound=XMLBaseModel, default=Feed)


class Atom(XMLBaseModel, Generic[FeedT]):
    """
    Atom 1.0 (https://validator.w3.org/feed/docs/atom.html).

    Generic over the feed type: ``Atom[Feed[MyEntry]]`` or ``Atom[MyFeed]``.
    """

    version: Tag[str] | None = Field(alias="@version", default=None)
    feed: Tag[FeedT]
