from pydantic import Field

from rss_parser import RSSParser
from rss_parser.models import XMLBaseModel
from rss_parser.models.rss import RSS, Channel, Item
from rss_parser.models.types.tag import Tag

PODCAST_XML = """<?xml version="1.0"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Title</title>
    <link>http://example.com</link>
    <description>Description</description>
    <itunes:author>Channel Author</itunes:author>
    <item>
      <title>Episode 1</title>
      <itunes:duration>3600</itunes:duration>
    </item>
  </channel>
</rss>"""


class DurationItem(Item):
    itunes_duration: Tag[str] | None = Field(alias="itunes:duration", default=None)


class TestGenericSchemas:
    def test_custom_item_is_one_parametrization_away(self):
        rss = RSSParser.parse(PODCAST_XML, schema=RSS[Channel[DurationItem]])

        item = rss.channel.content.items[0].content
        assert isinstance(item, DurationItem)
        assert item.itunes_duration.content == "3600"

    def test_custom_channel_subclass(self):
        class MyChannel(Channel[DurationItem]):
            itunes_author: Tag[str] | None = Field(alias="itunes:author", default=None)

        rss = RSSParser.parse(PODCAST_XML, schema=RSS[MyChannel])

        assert rss.channel.content.itunes_author.content == "Channel Author"
        assert rss.channel.content.items[0].content.itunes_duration.content == "3600"

    def test_default_parametrization_is_unchanged(self):
        rss = RSSParser.parse(PODCAST_XML)

        assert type(rss.channel.content.items[0].content) is Item


class TestUnknownTagsAreKept:
    def test_unknown_tags_end_up_in_model_extra(self):
        rss = RSSParser.parse(PODCAST_XML)

        assert rss.channel.content.model_extra["itunes:author"] == "Channel Author"
        assert rss.channel.content.items[0].content.model_extra["itunes:duration"] == "3600"


class TestCustomRootSchema:
    def test_schema_keyword_with_custom_root(self):
        class CustomSchema(XMLBaseModel):
            custom: Tag[str]

        rss = RSSParser.parse(
            '<rss version="2.0"><custom>Custom tag data</custom></rss>',
            schema=CustomSchema,
        )

        assert rss.custom.content == "Custom tag data"

    def test_populate_by_name(self):
        item = Item(title="hello")

        assert item.title.content == "hello"
