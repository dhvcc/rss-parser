# Podcasts (iTunes extensions)

Most real-world RSS is podcast feeds, and podcast feeds live and die by the
[Apple Podcasts (`itunes:*`) tags](https://podcasters.apple.com/support/823-podcast-requirements).
`rss-parser` ships typed support for them — no custom schema required.

## PodcastParser

```python
from rss_parser import PodcastParser

podcast = PodcastParser.parse(feed_xml)
channel = podcast.channel.content

channel.itunes_author                       # 'Wondery'
channel.itunes_type                         # 'serial'
channel.itunes_explicit                     # 'yes'
channel.itunes_image.attributes["href"]     # 'https://.../artwork.jpeg'
channel.itunes_owner.content.email          # 'iwonder@wondery.com'
channel.itunes_categories[0].attributes     # {'text': 'True Crime'}

episode = channel.items[0].content
episode.itunes_duration                     # '00:05:01' (seconds or HH:MM:SS - kept as str)
episode.itunes_episode                      # 1 (int)
episode.itunes_season                       # 1 (int)
episode.itunes_episode_type                 # 'trailer' | 'full' | 'bonus'
episode.itunes_image.attributes["href"]     # episode artwork url
```

With automatic feed detection:

```python
from rss_parser import parse, FeedType, PodcastParser

feed = parse(data, parsers={FeedType.RSS: PodcastParser})
```

## What's included

**Channel (show) level** — `itunes_author`, `itunes_type`, `itunes_title`, `itunes_subtitle`,
`itunes_summary`, `itunes_owner` (name + email), `itunes_image`, `itunes_categories`,
`itunes_explicit`, `itunes_keywords`, `itunes_new_feed_url`, `itunes_block`, `itunes_complete`.

**Item (episode) level** — `itunes_title`, `itunes_author`, `itunes_subtitle`, `itunes_summary`,
`itunes_duration`, `itunes_episode`, `itunes_season`, `itunes_episode_type`, `itunes_explicit`,
`itunes_image`, `itunes_keywords`, `itunes_block`.

## Composing with your own fields

The podcast schema is built from mixins, so you can combine it with your own extensions:

```python
from typing import Optional
from pydantic import Field

from rss_parser import RSSParser
from rss_parser.models.rss import RSS, Channel, Item
from rss_parser.models.rss.itunes import ITunesChannelMixin, ITunesItemMixin
from rss_parser.models.types import Tag


class MyEpisode(ITunesItemMixin, Item):
    podcast_transcript: Optional[Tag[dict]] = Field(alias="podcast:transcript", default=None)


class MyShow(ITunesChannelMixin, Channel[MyEpisode]):
    podcast_guid: Optional[Tag[str]] = Field(alias="podcast:guid", default=None)


podcast = RSSParser.parse(data, schema=RSS[MyShow])
```
