from typing import List, Optional

from pydantic import Field, validator

from rss_parser.models import RSSBaseModel
from rss_parser.models.image import Image
from rss_parser.models.item import Item
from rss_parser.models.text_input import TextInput
from rss_parser.models.types.date import DatetimeOrStr, validate_dt_or_str
from rss_parser.models.types.tag import Tag


class RequiredChannelElementsMixin(RSSBaseModel):
    """https://www.rssboard.org/rss-specification#requiredChannelElements."""

    title: str = None  # GoUpstate.com News Headlines
    "The name of the channel. It's how people refer to your service. If you have an HTML website that contains " "the same information as your RSS file, the title of your channel should be the same as the title of your " "website."  # noqa

    link: str = None  # http://www.goupstate.com/
    "The URL to the HTML website corresponding to the channel."

    description: Tag[str] = None  # The latest news from GoUpstate.com, a Spartanburg Herald-Journal Web site.
    "Phrase or sentence describing the channel."


class OptionalChannelElementsMixin(RSSBaseModel):
    """https://www.rssboard.org/rss-specification#optionalChannelElements."""

    items: Optional[List[Item]] = Field(alias="item", default=[])

    language: Optional[str] = None  # en-us
    "The language the channel is written in. This allows aggregators to group all Italian language sites, " "for example, on a single page."  # noqa

    copyright: Optional[str] = None  # Copyright 2002, Spartanburg Herald-Journal  # noqa
    "Copyright notice for content in the channel."

    managing_editor: Optional[str] = None  # geo@herald.com (George Matesky)
    "Email address for person responsible for editorial content."

    web_master: Optional[str] = None  # betty@herald.com (Betty Guernsey)
    "Email address for person responsible for technical issues relating to channel."

    pub_date: Optional[Tag[DatetimeOrStr]] = None  # Sat, 07 Sep 2002 00:00:01 GMT
    "The publication date for the content in the channel. For example, the New York Times publishes on a daily " "basis, the publication date flips once every 24 hours. That's when the pubDate of the channel changes. All " "date-times in RSS conform to the Date and Time Specification of RFC 822, with the exception that the year " "may be expressed with two characters or four characters (four preferred)."  # noqa

    last_build_date: Optional[DatetimeOrStr] = None  # Sat, 07 Sep 2002 09:42:31 GMT
    "The last time the content of the channel changed."

    category: Optional[Tag[str]] = None  # Newspapers
    "Specify one or more categories that the channel belongs to. Follows the same rules as the <item.py>-level " "category element."  # noqa

    generator: Optional[str] = None  # MightyInHouse Content System v2.3
    "A string indicating the program used to generate the channel."

    docs: Optional[str] = None  # https://www.rssboard.org/rss-specification
    "A URL that points to the documentation for the format used in the RSS file. It's probably a pointer to this " "page. It's for people who might stumble across an RSS file on a Web server 25 years from now and wonder what " "it is."  # noqa

    # TODO: should support self-closing tags with their attributes?
    cloud: Optional[str] = None  # <cloud domain="rpc.sys.com" protocol="soap"/>
    "Allows processes to register with a cloud to be notified of updates to the channel, implementing a lightweight " "publish-subscribe protocol for RSS feeds."  # noqa

    ttl: Optional[str] = None  # 60
    "ttl stands for time to live. It's a number of minutes that indicates how long a channel can be cached before " "refreshing from the source."  # noqa

    image: Optional[Image] = None
    "Specifies a GIF, JPEG or PNG image that can be displayed with the channel."

    rating: Optional[TextInput] = None
    "The PICS rating for the channel."

    text_input: Optional[str] = None
    "Specifies a text input box that can be displayed with the channel."

    skip_hours: Optional[str] = None
    "A hint for aggregators telling them which hours they can skip. This element contains up to 24 <hour> " "sub-elements whose value is a number between 0 and 23, representing a time in GMT, when aggregators, if " "they support the feature, may not read the channel on hours listed in the <skipHours> element. The hour " "beginning at midnight is hour zero."  # noqa

    skip_days: Optional[str] = None
    "A hint for aggregators telling them which days they can skip. This element contains up to seven <day> " "sub-elements whose value is Monday, Tuesday, Wednesday, Thursday, Friday, Saturday or Sunday. Aggregators " "may not read the channel during days listed in the <skipDays> element."  # noqa

    # types
    _normalize_pub_date = validator("pub_date", allow_reuse=True)(validate_dt_or_str)
    _normalize_last_build_date = validator("last_build_date", allow_reuse=True)(validate_dt_or_str)


class Channel(RequiredChannelElementsMixin, OptionalChannelElementsMixin):
    pass
