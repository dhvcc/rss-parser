from datetime import datetime

import pytest
from pydantic import ValidationError

from rss_parser import RSSParser

CHANNEL_TEMPLATE = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Title</title>
    <link>http://example.com</link>
    <description>Description</description>
    {extra}
  </channel>
</rss>"""


def parse_channel(extra: str = ""):
    return RSSParser.parse(CHANNEL_TEMPLATE.format(extra=extra)).channel.content


class TestItemOptionality:
    """All elements of an <item> are optional, but at least one of title or description is required."""

    def test_title_only_item(self):
        channel = parse_channel("<item><title>only title</title></item>")

        assert channel.items[0].content.title.content == "only title"
        assert channel.items[0].content.description is None

    def test_description_only_item(self):
        channel = parse_channel("<item><description>only description</description></item>")

        assert channel.items[0].content.description.content == "only description"
        assert channel.items[0].content.title is None

    def test_empty_item_is_rejected(self):
        with pytest.raises(ValidationError, match="either <title> or <description>"):
            parse_channel("<item><guid>id-1</guid></item>")


class TestChannelElements:
    def test_managing_editor(self):
        channel = parse_channel("<managingEditor>geo@herald.com (George Matesky)</managingEditor>")

        assert channel.managing_editor.content == "geo@herald.com (George Matesky)"

    def test_skip_hours_and_days(self):
        channel = parse_channel(
            "<skipHours><hour>0</hour><hour>23</hour></skipHours>"
            "<skipDays><day>Saturday</day><day>Sunday</day></skipDays>"
        )

        assert [hour.content for hour in channel.skip_hours.content.hours] == [0, 23]
        assert [day.content for day in channel.skip_days.content.days] == ["Saturday", "Sunday"]

    def test_single_skip_hour_is_still_a_list(self):
        channel = parse_channel("<skipHours><hour>12</hour></skipHours>")

        assert [hour.content for hour in channel.skip_hours.content.hours] == [12]

    def test_text_input_is_a_model(self):
        channel = parse_channel(
            "<textInput><title>Submit</title><description>Search</description>"
            "<name>q</name><link>http://example.com/search</link></textInput>"
        )

        assert channel.text_input.content.name.content == "q"
        assert channel.text_input.content.link.content == "http://example.com/search"

    def test_rating_is_a_string(self):
        channel = parse_channel("<rating>(PICS-1.1 &quot;http://www.rsac.org/ratingsv01.html&quot;)</rating>")

        assert channel.rating.content.startswith("(PICS-1.1")

    def test_self_closing_list_tag_is_an_empty_list(self):
        channel = parse_channel("<category/>")

        assert channel.categories == []

    def test_ttl_is_an_int(self):
        channel = parse_channel("<ttl>60</ttl>")

        assert channel.ttl.content == 60

    def test_item_pub_date_is_parsed_to_datetime(self):
        channel = parse_channel("<item><title>t</title><pubDate>Sat, 07 Sep 2002 00:00:01 GMT</pubDate></item>")

        assert isinstance(channel.items[0].content.pub_date.content, datetime)


class TestRSSVersions:
    def test_rss_0_91_parses_with_version(self):
        rss = RSSParser.parse(
            '<rss version="0.91"><channel><title>T</title><link>L</link><description>D</description></channel></rss>'
        )

        assert rss.version.content == "0.91"
