import json

from rss_parser import RSSParser

XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Title</title>
    <link>http://example.com</link>
    <description>Description</description>
    <ttl>60</ttl>
    <item>
      <title>Item 1</title>
      <guid isPermaLink="false">id-1</guid>
      <pubDate>Sat, 07 Sep 2002 00:00:01 GMT</pubDate>
    </item>
  </channel>
</rss>"""


class TestModelDump:
    def test_model_dump_keeps_tag_structure(self):
        rss = RSSParser.parse(XML)
        dump = rss.model_dump()

        assert dump["channel"]["content"]["title"]["content"] == "Title"
        assert dump["channel"]["content"]["items"][0]["content"]["guid"]["attributes"] == {"is_perma_link": "false"}

    def test_model_dump_json_round_trips(self):
        rss = RSSParser.parse(XML)

        assert json.loads(rss.model_dump_json())["version"]["content"] == "2.0"


class TestPlainSerialization:
    def test_dict_plain_flattens_tags_to_content(self):
        rss = RSSParser.parse(XML)
        plain = rss.dict_plain()

        assert plain["version"] == "2.0"
        assert plain["channel"]["title"] == "Title"
        assert plain["channel"]["ttl"] == 60
        assert plain["channel"]["items"][0]["title"] == "Item 1"

    def test_dict_plain_serializes_datetimes(self):
        plain = RSSParser.parse(XML).dict_plain()

        assert plain["channel"]["items"][0]["pub_date"] == "2002-09-07T00:00:01Z"

    def test_json_plain_matches_dict_plain(self):
        rss = RSSParser.parse(XML)

        assert json.loads(rss.json_plain()) == rss.dict_plain()

    def test_unknown_tags_survive_serialization(self):
        rss = RSSParser.parse(XML.replace("<ttl>60</ttl>", "<custom:tag>kept</custom:tag>"))

        assert rss.model_dump()["channel"]["content"]["custom:tag"] == "kept"
        assert rss.dict_plain()["channel"]["custom:tag"] == "kept"
