"""
Apple Podcasts (iTunes) RSS extensions.

https://podcasters.apple.com/support/823-podcast-requirements

Use the ready-made ``Podcast`` schema (or ``PodcastParser``) for a typical podcast feed,
or mix ``ITunesChannelMixin``/``ITunesItemMixin`` into your own schemas.
"""

from pydantic import Field

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss.channel import Channel
from rss_parser.models.rss.item import Item
from rss_parser.models.rss.rss import RSS
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag


class ITunesOwner(XMLBaseModel):
    """<itunes:owner> - contact information for the podcast owner."""

    name: Tag[str] | None = Field(alias="itunes:name", default=None)
    "The name of the podcast owner."

    email: Tag[str] | None = Field(alias="itunes:email", default=None)
    "The email address of the podcast owner."


class ITunesItemMixin(XMLBaseModel):
    """Mix into an RSS item schema to get typed access to episode-level itunes:* tags."""

    itunes_title: Tag[str] | None = Field(alias="itunes:title", default=None)
    "An episode title specific for Apple Podcasts, without season/episode numbers."

    itunes_author: Tag[str] | None = Field(alias="itunes:author", default=None)
    "The group, person, or people responsible for creating the episode."

    itunes_subtitle: Tag[str] | None = Field(alias="itunes:subtitle", default=None)
    "A short description of the episode."

    itunes_summary: Tag[str] | None = Field(alias="itunes:summary", default=None)
    "A longer description of the episode."

    itunes_duration: Tag[str] | None = Field(alias="itunes:duration", default=None)
    "The duration of the episode - either in seconds or as HH:MM:SS, so it's kept as a string."

    itunes_episode: Tag[int] | None = Field(alias="itunes:episode", default=None)
    "The episode number."

    itunes_season: Tag[int] | None = Field(alias="itunes:season", default=None)
    "The season number."

    itunes_episode_type: Tag[str] | None = Field(alias="itunes:episodeType", default=None)
    "The episode type: full, trailer, or bonus."

    itunes_explicit: Tag[str] | None = Field(alias="itunes:explicit", default=None)
    "The episode parental advisory information: true/false (or the legacy yes/no/clean)."

    itunes_image: Tag[str] | None = Field(alias="itunes:image", default=None)
    "The episode artwork. The tag is attribute-only - the url lives in `.attributes['href']`."

    itunes_keywords: Tag[str] | None = Field(alias="itunes:keywords", default=None)
    "A comma-separated list of keywords (legacy tag, still common in the wild)."

    itunes_block: Tag[str] | None = Field(alias="itunes:block", default=None)
    "The episode show or hide status - 'Yes' prevents the episode from appearing in Apple Podcasts."


class ITunesChannelMixin(XMLBaseModel):
    """Mix into an RSS channel schema to get typed access to show-level itunes:* tags."""

    itunes_author: Tag[str] | None = Field(alias="itunes:author", default=None)
    "The group, person, or people responsible for creating the show."

    itunes_type: Tag[str] | None = Field(alias="itunes:type", default=None)
    "The type of show: episodic or serial."

    itunes_title: Tag[str] | None = Field(alias="itunes:title", default=None)
    "A show title specific for Apple Podcasts."

    itunes_subtitle: Tag[str] | None = Field(alias="itunes:subtitle", default=None)
    "A short description of the show."

    itunes_summary: Tag[str] | None = Field(alias="itunes:summary", default=None)
    "A longer description of the show."

    itunes_owner: Tag[ITunesOwner] | None = Field(alias="itunes:owner", default=None)
    "The podcast owner contact information."

    itunes_image: Tag[str] | None = Field(alias="itunes:image", default=None)
    "The show artwork. The tag is attribute-only - the url lives in `.attributes['href']`."

    itunes_categories: OnlyList[Tag[dict]] = Field(alias="itunes:category", default_factory=OnlyList)
    "The show categories. Attribute-only tags, possibly nested - the category name lives in `.attributes['text']`."

    itunes_explicit: Tag[str] | None = Field(alias="itunes:explicit", default=None)
    "The show parental advisory information: true/false (or the legacy yes/no/clean)."

    itunes_keywords: Tag[str] | None = Field(alias="itunes:keywords", default=None)
    "A comma-separated list of keywords (legacy tag, still common in the wild)."

    itunes_new_feed_url: Tag[str] | None = Field(alias="itunes:new-feed-url", default=None)
    "The new podcast RSS feed URL, used when moving a feed."

    itunes_block: Tag[str] | None = Field(alias="itunes:block", default=None)
    "The show or hide status - 'Yes' prevents the whole podcast from appearing in Apple Podcasts."

    itunes_complete: Tag[str] | None = Field(alias="itunes:complete", default=None)
    "The podcast update status - 'Yes' means the podcast is complete and no new episodes will be published."


class ITunesItem(ITunesItemMixin, Item):
    """RSS 2.0 item + episode-level Apple Podcasts tags."""


class ITunesChannel(ITunesChannelMixin, Channel[ITunesItem]):
    """RSS 2.0 channel + show-level Apple Podcasts tags, with ITunesItem items."""


class Podcast(RSS[ITunesChannel]):
    """A ready-made schema for podcast feeds: RSS 2.0 + Apple Podcasts extensions."""
