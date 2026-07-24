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

    def test_dict_plain_by_alias_uses_alias_keys(self):
        plain = RSSParser.parse(XML).dict_plain(by_alias=True)

        assert plain["@version"] == "2.0"
        item = plain["channel"]["item"][0]
        assert item["title"] == "Item 1"
        assert item["pubDate"] == "2002-09-07T00:00:01Z"
        assert item["guid"] == "id-1"

    def test_json_plain_by_alias_matches_dict_plain(self):
        rss = RSSParser.parse(XML)

        assert json.loads(rss.json_plain(by_alias=True)) == rss.dict_plain(by_alias=True)

    def test_dict_plain_exclude_defaults_still_flattens_tags(self):
        plain = RSSParser.parse(XML).dict_plain(exclude_defaults=True)

        assert plain["version"] == "2.0"
        assert plain["channel"]["title"] == "Title"
        # guid keeps non-default attributes in the dump, but is still flattened to its content
        assert plain["channel"]["items"][0]["guid"] == "id-1"


class TestJsonPlainEncoderOptions:
    def test_indent_is_passed_to_the_json_encoder(self):
        rss = RSSParser.parse(XML)
        pretty = rss.json_plain(indent=2)

        assert '\n  "version": "2.0"' in pretty
        assert json.loads(pretty) == rss.dict_plain()

    def test_sort_keys_and_separators(self):
        rss = RSSParser.parse(XML)
        compact = rss.json_plain(sort_keys=True, separators=(",", ":"))

        assert '"version":"2.0"' in compact
        assert json.loads(compact) == rss.dict_plain()

    def test_ensure_ascii(self):
        rss = RSSParser.parse(XML.replace("<title>Title</title>", "<title>Тайтл</title>"))

        assert '"Тайтл"' in rss.json_plain()
        assert "\\u0422" in rss.json_plain(ensure_ascii=True)

    def test_encoder_options_combine_with_dump_options(self):
        rss = RSSParser.parse(XML)

        assert json.loads(rss.json_plain(indent=2, by_alias=True)) == rss.dict_plain(by_alias=True)


class TestDumpRoundTrip:
    def test_model_validate_model_dump_round_trips(self):
        rss = RSSParser.parse(XML)

        assert type(rss).model_validate(rss.model_dump()) == rss

    def test_model_validate_exclude_defaults_dump_round_trips(self):
        rss = RSSParser.parse(XML)
        again = type(rss).model_validate(rss.model_dump(exclude_defaults=True))

        assert again == rss

    def test_json_dump_round_trips(self):
        rss = RSSParser.parse(XML)
        again = type(rss).model_validate(json.loads(rss.model_dump_json(exclude_defaults=True)))

        assert again.channel.content.items[0].content.guid.content == "id-1"
        assert again.channel.content.items[0].content.guid.attributes == {"is_perma_link": "false"}
