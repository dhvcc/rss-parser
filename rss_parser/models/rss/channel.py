from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss.image import Image
from rss_parser.models.rss.item import Item
from rss_parser.models.rss.text_input import TextInput
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class RequiredChannelElementsMixin(XMLBaseModel):
    """https://www.rssboard.org/rss-specification#requiredChannelElements."""

    title: Tag[str] = None  # GoUpstate.com News Headlines
    "The name of the channel. It's how people refer to your service. If you have an HTML website that contains " "the same information as your RSS file, the title of your channel should be the same as the title of your " "website."  # noqa

    link: Tag[str] = None  # http://www.goupstate.com/
    "The URL to the HTML website corresponding to the channel."

    description: Tag[str] = None  # The latest news from GoUpstate.com, a Spartanburg Herald-Journal Web site.
    "Phrase or sentence describing the channel."


class OptionalChannelElementsMixin(XMLBaseModel):
    """https://www.rssboard.org/rss-specification#optionalChannelElements."""

    items: Optional[OnlyList[Tag[Item]]] = pydantic.Field(alias="item", default=[])

    language: Optional[Tag[str]] = None  # en-us
    "The language the channel is written in. This allows aggregators to group all Italian language sites, " "for example, on a single page."  # noqa

    copyright: Optional[Tag[str]] = None  # Copyright 2002, Spartanburg Herald-Journal  # noqa
    "Copyright notice for content in the channel."

    "Email address for person responsible for editorial content."

    web_master: Optional[Tag[str]] = None  # betty@herald.com (Betty Guernsey)
    "Email address for person responsible for technical issues relating to channel."

    pub_date: Optional[Tag[DateTimeOrStr]] = None  # Sat, 07 Sep 2002 00:00:01 GMT
    "The publication date for the content in the channel. For example, the New York Times publishes on a daily " "basis, the publication date flips once every 24 hours. That's when the pubDate of the channel changes. All " "date-times in RSS conform to the Date and Time Specification of RFC 822, with the exception that the year " "may be expressed with two characters or four characters (four preferred)."  # noqa

    last_build_date: Optional[Tag[DateTimeOrStr]] = None  # Sat, 07 Sep 2002 09:42:31 GMT
    "The last time the content of the channel changed."

    categories: Optional[OnlyList[Tag[str]]] = pydantic.Field(alias="category", default=[])
    "Specify one or more categories that the channel belongs to. Follows the same rules as the <item.py>-level " "category element."  # noqa

    generator: Optional[Tag[str]] = None  # MightyInHouse Content System v2.3
    "A string indicating the program used to generate the channel."

    docs: Optional[Tag[str]] = None  # https://www.rssboard.org/rss-specification
    "A URL that points to the documentation for the format used in the RSS file. It's probably a pointer to this " "page. It's for people who might stumble across an RSS file on a Web server 25 years from now and wonder what " "it is."  # noqa

    cloud: Optional[Tag[str]] = None  # <cloud domain="rpc.sys.com" protocol="soap"/>
    "Allows processes to register with a cloud to be notified of updates to the channel, implementing a lightweight " "publish-subscribe protocol for RSS feeds."  # noqa

    ttl: Optional[Tag[str]] = None  # 60
    "ttl stands for time to live. It's a number of minutes that indicates how long a channel can be cached before " "refreshing from the source."  # noqa

    image: Optional[Tag[Image]] = None
    "Specifies a GIF, JPEG or PNG image that can be displayed with the channel."

    rating: Optional[Tag[TextInput]] = None
    "The PICS rating for the channel."

    text_input: Optional[Tag[str]] = None
    "Specifies a text input box that can be displayed with the channel."

    skip_hours: Optional[Tag[str]] = None
    "A hint for aggregators telling them which hours they can skip. This element contains up to 24 <hour> " "sub-elements whose value is a number between 0 and 23, representing a time in GMT, when aggregators, if " "they support the feature, may not read the channel on hours listed in the <skipHours> element. The hour " "beginning at midnight is hour zero."  # noqa

    skip_days: Optional[Tag[str]] = None
    "A hint for aggregators telling them which days they can skip. This element contains up to seven <day> " "sub-elements whose value is Monday, Tuesday, Wednesday, Thursday, Friday, Saturday or Sunday. Aggregators " "may not read the channel during days listed in the <skipDays> element."  # noqa


class Channel(RequiredChannelElementsMixin, OptionalChannelElementsMixin, XMLBaseModel):
    pass
