from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class TextInput(XMLBaseModel):
    """
    The purpose of the <textInput> element is something of a mystery. You can use it to specify a search engine box.
    Or to allow a reader to provide feedback. Most aggregators ignore it.

    https://www.rssboard.org/rss-specification#lttextinputgtSubelementOfLtchannelgt
    """

    title: Tag[str] = None
    "The label of the Submit button in the text input area."

    description: Tag[str] = None
    "Explains the text input area."

    name: Tag[str] = None
    "The name of the text object in the text input area."

    link: Tag[str] = None
    "The URL of the CGI script that processes text input requests."
