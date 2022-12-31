from rss_parser.models import RSSBaseModel


class TextInput(RSSBaseModel):
    """
    The purpose of the <textInput> element is something of a mystery. You can use it to specify a search engine box.
    Or to allow a reader to provide feedback. Most aggregators ignore it.

    https://www.rssboard.org/rss-specification#lttextinputgtSubelementOfLtchannelgt
    """

    title: str = None
    "The label of the Submit button in the text input area."

    description: str = None
    "Explains the text input area."

    name: str = None
    "The name of the text object in the text input area."

    link: str = None
    "The URL of the CGI script that processes text input requests."
