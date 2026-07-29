from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class RDFChannel(XMLBaseModel):
    """
    RSS 1.0 <channel> (https://web.resource.org/rss/1.0/spec#s5.3).

    Note that in RSS 1.0 the actual items live *next to* the channel, not inside it -
    see ``RDF.items``. The channel's <items> rdf:Seq table of contents, along with any
    other non-core tags (dc:*, syn:*), is kept in `model_extra`.
    """

    title: Tag[str]
    "A descriptive title for the channel."

    link: Tag[str]
    "The URL to which an HTML rendering of the channel title will link."

    description: Tag[str]
    "A brief description of the channel's content, function, source, etc."

    image: Tag[dict] | None = None
    "An rdf:resource reference to the channel image, if any."

    text_input: Tag[dict] | None = Field(alias="textinput", default=None)
    "An rdf:resource reference to the channel textinput, if any."
