from pathlib import Path

from rss_parser import PodcastParser
from rss_parser.models.rss.itunes import ITunesChannel, ITunesItem

APOLOGY_LINE = (Path(__file__).parent / "samples" / "podcast" / "apology_line" / "data.xml").read_text(encoding="utf-8")

PODCAST_XML = """<?xml version="1.0"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>The Show</title>
    <link>http://example.com</link>
    <description>A show</description>
    <itunes:author>Jane Host</itunes:author>
    <itunes:type>serial</itunes:type>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="http://example.com/art.jpg"/>
    <itunes:category text="Comedy"/>
    <itunes:category text="Society &amp; Culture">
      <itunes:category text="Documentary"/>
    </itunes:category>
    <itunes:owner>
      <itunes:name>Jane Host</itunes:name>
      <itunes:email>jane@example.com</itunes:email>
    </itunes:owner>
    <item>
      <title>Pilot</title>
      <itunes:title>Pilot</itunes:title>
      <itunes:duration>31:07</itunes:duration>
      <itunes:episode>1</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:image href="http://example.com/ep1.jpg"/>
    </item>
  </channel>
</rss>"""


class TestPodcastSchema:
    def test_channel_level_tags(self):
        podcast = PodcastParser.parse(PODCAST_XML)
        channel = podcast.channel.content

        assert isinstance(channel, ITunesChannel)
        assert channel.itunes_author.content == "Jane Host"
        assert channel.itunes_type.content == "serial"
        assert channel.itunes_explicit.content == "false"
        assert channel.itunes_image.attributes == {"href": "http://example.com/art.jpg"}
        assert channel.itunes_owner.content.name.content == "Jane Host"
        assert channel.itunes_owner.content.email.content == "jane@example.com"

    def test_categories_including_nested(self):
        channel = PodcastParser.parse(PODCAST_XML).channel.content

        assert channel.itunes_categories[0].attributes == {"text": "Comedy"}
        # The nested category is kept raw in the content
        assert channel.itunes_categories[1].attributes["text"] == "Society & Culture"

    def test_episode_level_tags(self):
        item = PodcastParser.parse(PODCAST_XML).channel.content.items[0].content

        assert isinstance(item, ITunesItem)
        assert item.itunes_duration.content == "31:07"
        assert item.itunes_episode.content == 1
        assert item.itunes_season.content == 1
        assert item.itunes_episode_type.content == "full"
        assert item.itunes_image.attributes == {"href": "http://example.com/ep1.jpg"}

    def test_real_world_feed(self):
        podcast = PodcastParser.parse(APOLOGY_LINE)
        channel = podcast.channel.content

        assert channel.itunes_author.content == "Wondery"
        assert channel.itunes_owner.content.email.content == "iwonder@wondery.com"
        assert channel.itunes_categories[0].attributes == {"text": "True Crime"}
        assert channel.items[0].content.itunes_episode_type.content == "trailer"
        assert all(item.content.itunes_duration is not None for item in channel.items)
