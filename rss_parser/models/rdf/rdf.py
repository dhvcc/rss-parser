from typing import Generic

from pydantic import Field
from typing_extensions import TypeVar

from rss_parser.models import XMLBaseModel
from rss_parser.models.rdf.channel import RDFChannel
from rss_parser.models.rdf.item import RDFItem
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag

RDFChannelT = TypeVar("RDFChannelT", bound=XMLBaseModel, default=RDFChannel)
RDFItemT = TypeVar("RDFItemT", bound=XMLBaseModel, default=RDFItem)


class RDF(XMLBaseModel, Generic[RDFChannelT, RDFItemT]):
    """
    RSS 1.0 - RDF Site Summary (https://web.resource.org/rss/1.0/spec).

    Unlike RSS 2.0, the items are siblings of the channel, not children of it.

    Generic over the channel and item types: ``RDF[MyChannel, MyItem]``.
    """

    channel: Tag[RDFChannelT]
    items: OnlyList[Tag[RDFItemT]] = Field(alias="item", default_factory=OnlyList)

    image: Tag[dict] | None = None
    "The channel image, if any."

    text_input: Tag[dict] | None = Field(alias="textinput", default=None)
    "The channel textinput, if any."
