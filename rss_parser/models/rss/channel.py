from typing import Generic

from pydantic import Field
from typing_extensions import TypeVar

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss.image import Image
from rss_parser.models.rss.item import Item
from rss_parser.models.rss.skip import SkipDays, SkipHours
from rss_parser.models.rss.text_input import TextInput
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag

ItemT = TypeVar("ItemT", bound=XMLBaseModel, default=Item)


class Channel(XMLBaseModel, Generic[ItemT]):
    """
    https://www.rssboard.org/rss-specification#requiredChannelElements

    Generic over the item type, so a custom item schema is one parametrization away:
    ``Channel[MyItem]``.
    """

    # Required channel elements

    title: Tag[str]  # GoUpstate.com News Headlines
    "The name of the channel. It's how people refer to your service. If you have an HTML website that contains the same information as your RSS file, the title of your channel should be the same as the title of your website."  # noqa: E501

    link: Tag[str]  # http://www.goupstate.com/
    "The URL to the HTML website corresponding to the channel."

    description: Tag[str]  # The latest news from GoUpstate.com, a Spartanburg Herald-Journal Web site.
    "Phrase or sentence describing the channel."

    # Optional channel elements
    # https://www.rssboard.org/rss-specification#optionalChannelElements

    items: OnlyList[Tag[ItemT]] = Field(alias="item", default_factory=OnlyList)

    language: Tag[str] | None = None  # en-us
    "The language the channel is written in. This allows aggregators to group all Italian language sites, for example, on a single page."  # noqa: E501

    copyright: Tag[str] | None = None  # Copyright 2002, Spartanburg Herald-Journal
    "Copyright notice for content in the channel."

    managing_editor: Tag[str] | None = None  # geo@herald.com (George Matesky)
    "Email address for person responsible for editorial content."

    web_master: Tag[str] | None = None  # betty@herald.com (Betty Guernsey)
    "Email address for person responsible for technical issues relating to channel."

    pub_date: Tag[DateTimeOrStr] | None = None  # Sat, 07 Sep 2002 00:00:01 GMT
    "The publication date for the content in the channel. For example, the New York Times publishes on a daily basis, the publication date flips once every 24 hours. That's when the pubDate of the channel changes. All date-times in RSS conform to the Date and Time Specification of RFC 822, with the exception that the year may be expressed with two characters or four characters (four preferred)."  # noqa: E501

    last_build_date: Tag[DateTimeOrStr] | None = None  # Sat, 07 Sep 2002 09:42:31 GMT
    "The last time the content of the channel changed."

    categories: OnlyList[Tag[str]] = Field(alias="category", default_factory=OnlyList)
    "Specify one or more categories that the channel belongs to. Follows the same rules as the <item>-level category element."  # noqa: E501

    generator: Tag[str] | None = None  # MightyInHouse Content System v2.3
    "A string indicating the program used to generate the channel."

    docs: Tag[str] | None = None  # https://www.rssboard.org/rss-specification
    "A URL that points to the documentation for the format used in the RSS file. It's probably a pointer to this page. It's for people who might stumble across an RSS file on a Web server 25 years from now and wonder what it is."  # noqa: E501

    cloud: Tag[str] | None = None  # <cloud domain="rpc.sys.com" protocol="soap"/>
    "Allows processes to register with a cloud to be notified of updates to the channel, implementing a lightweight publish-subscribe protocol for RSS feeds. The tag is attribute-only - see `.attributes`."  # noqa: E501

    ttl: Tag[int] | None = None  # 60
    "ttl stands for time to live. It's a number of minutes that indicates how long a channel can be cached before refreshing from the source."  # noqa: E501

    image: Tag[Image] | None = None
    "Specifies a GIF, JPEG or PNG image that can be displayed with the channel."

    rating: Tag[str] | None = None
    "The PICS rating for the channel."

    text_input: Tag[TextInput] | None = None
    "Specifies a text input box that can be displayed with the channel."

    skip_hours: Tag[SkipHours] | None = None
    "A hint for aggregators telling them which hours they can skip. This element contains up to 24 <hour> sub-elements whose value is a number between 0 and 23, representing a time in GMT, when aggregators, if they support the feature, may not read the channel on hours listed in the <skipHours> element. The hour beginning at midnight is hour zero."  # noqa: E501

    skip_days: Tag[SkipDays] | None = None
    "A hint for aggregators telling them which days they can skip. This element contains up to seven <day> sub-elements whose value is Monday, Tuesday, Wednesday, Thursday, Friday, Saturday or Sunday. Aggregators may not read the channel during days listed in the <skipDays> element."  # noqa: E501
