from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class RDFItem(XMLBaseModel):
    """
    RSS 1.0 <item> (https://web.resource.org/rss/1.0/spec#s5.5).

    Non-core tags (e.g. dc:*) are kept in `model_extra`.
    The rdf:about identifier lives in `.attributes` of the wrapping Tag.
    """

    title: Tag[str]
    "The item's title."

    link: Tag[str]
    "The item's URL."

    description: Optional[Tag[str]] = None
    "A brief description/abstract of the item."
