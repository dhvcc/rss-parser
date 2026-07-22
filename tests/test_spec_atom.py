from datetime import datetime

import pytest
from pydantic import ValidationError

from rss_parser import AtomParser
from rss_parser.models.atom.entry import Entry
from rss_parser.models.atom.source import Source

FEED_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>
  <title>Example Feed</title>
  <updated>2003-12-13T18:30:02Z</updated>
  {extra}
</feed>"""


def parse_feed(extra: str = ""):
    return AtomParser.parse(FEED_TEMPLATE.format(extra=extra)).feed.content


class TestFeedElements:
    def test_required_elements(self):
        feed = parse_feed()

        assert feed.id.content == "urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6"
        assert feed.title.content == "Example Feed"
        assert isinstance(feed.updated.content, datetime)

    def test_feed_without_id_is_rejected(self):
        with pytest.raises(ValidationError, match="id"):
            AtomParser.parse('<feed xmlns="http://www.w3.org/2005/Atom"><title>T</title></feed>')

    def test_feed_without_updated_is_accepted(self):
        """The spec requires <updated>, but major publishers (YouTube) omit it."""
        feed = AtomParser.parse(
            '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:x</id><title>T</title></feed>'
        ).feed.content

        assert feed.updated is None

    def test_multiple_authors_and_links(self):
        feed = parse_feed(
            "<author><name>Ann</name><email>ann@example.com</email></author>"
            "<author><name>Bob</name></author>"
            '<link rel="self" href="http://example.com/feed"/>'
            '<link rel="alternate" href="http://example.com"/>'
        )

        assert [str(a.content.name) for a in feed.authors] == ["Ann", "Bob"]
        assert feed.authors[0].content.email.content == "ann@example.com"
        assert [link.attributes["href"] for link in feed.links] == [
            "http://example.com/feed",
            "http://example.com",
        ]

    def test_single_link_is_still_a_list(self):
        feed = parse_feed('<link href="http://example.com"/>')

        assert len(feed.links) == 1


class TestEntryElements:
    def test_entry_fields(self):
        feed = parse_feed(
            "<entry>"
            "<id>urn:entry:1</id>"
            "<title>Entry title</title>"
            "<updated>2003-12-13T18:30:02Z</updated>"
            "<published>2003-12-12T18:30:02Z</published>"
            "<summary>Some text.</summary>"
            '<content type="html">&lt;p&gt;Body&lt;/p&gt;</content>'
            "</entry>"
        )
        entry = feed.entries[0].content

        assert isinstance(entry, Entry)
        assert entry.id.content == "urn:entry:1"
        assert isinstance(entry.updated.content, datetime)
        assert isinstance(entry.published.content, datetime)
        assert entry.summary.content == "Some text."
        assert entry.content.content == "<p>Body</p>"
        assert entry.content.attributes == {"type": "html"}

    def test_entry_without_title_is_rejected(self):
        with pytest.raises(ValidationError, match="title"):
            parse_feed("<entry><id>urn:entry:1</id></entry>")

    def test_entry_source_is_a_model(self):
        feed = parse_feed(
            "<entry>"
            "<id>urn:entry:1</id>"
            "<title>Copied entry</title>"
            "<source><id>urn:feed:orig</id><title>Original feed</title>"
            "<updated>2003-12-13T18:30:02Z</updated></source>"
            "</entry>"
        )
        source = feed.entries[0].content.source.content

        assert isinstance(source, Source)
        assert source.title.content == "Original feed"
