import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from rss_parser import AtomParser
from rss_parser.models.atom import Atom
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


class TestTextConstructs:
    """
    RFC 4287 3.1: text constructs may be type="text", type="html" or type="xhtml".

    For xhtml the field keeps the xmltodict mapping of the child elements. It is deliberately
    not re-serialized to markup: xmltodict collapses each element's text runs into one #text
    value and emits child elements first, so any round-trip silently reorders prose.
    """

    XHTML_CONTENT = (
        '<content type="xhtml">'
        '<div xmlns="http://www.w3.org/1999/xhtml"><p>Hello</p><ul><li>one</li></ul></div>'
        "</content>"
    )

    def _entry(self, *, extra: str) -> Entry:
        feed = parse_feed(f"<entry><id>urn:entry:1</id><title>T</title>{extra}</entry>")
        return feed.entries[0].content

    def test_xhtml_content_is_the_element_mapping(self):
        entry = self._entry(extra=self.XHTML_CONTENT)

        assert entry.content.attributes == {"type": "xhtml"}
        assert entry.content.content == {
            "div": {"@xmlns": "http://www.w3.org/1999/xhtml", "p": "Hello", "ul": {"li": "one"}}
        }

    def test_the_type_attribute_is_not_duplicated_into_the_content(self):
        entry = self._entry(extra=self.XHTML_CONTENT)

        assert "@type" not in entry.content.content

    def test_xhtml_summary_is_the_element_mapping(self):
        entry = self._entry(extra='<summary type="xhtml"><div><b>bold</b></div></summary>')

        assert entry.summary.attributes == {"type": "xhtml"}
        assert entry.summary.content == {"div": {"b": "bold"}}

    def test_xhtml_entry_title_is_the_element_mapping(self):
        feed = parse_feed(
            '<entry><id>urn:entry:1</id><title type="xhtml"><div><em>Ti</em></div></title></entry>',
        )
        title = feed.entries[0].content.title

        assert title.attributes == {"type": "xhtml"}
        assert title.content == {"div": {"em": "Ti"}}

    def test_xhtml_entry_rights_is_the_element_mapping(self):
        entry = self._entry(extra='<rights type="xhtml"><div>&#169; 2003</div></rights>')

        assert entry.rights.content == {"div": "© 2003"}

    @pytest.mark.parametrize("field", ["title", "subtitle", "rights"])
    def test_xhtml_feed_level_constructs(self, field):
        data = FEED_TEMPLATE.format(extra="").replace(
            "<title>Example Feed</title>",
            f'<{field} type="xhtml"><div><p>Marked up</p></div></{field}>'
            + ("" if field == "title" else "<title>Example Feed</title>"),
        )
        feed = AtomParser.parse(data).feed.content

        tag = getattr(feed, field)
        assert tag.attributes == {"type": "xhtml"}
        assert tag.content == {"div": {"p": "Marked up"}}

    def test_mixed_inline_markup_keeps_its_pieces_but_not_their_order(self):
        """Why the mapping is handed over raw: markup would read 'the docsRead  before shipping.'"""
        entry = self._entry(
            extra='<content type="xhtml"><div><p>Read <a href="http://x">the docs</a> before shipping.</p></div>'
            "</content>"
        )

        assert entry.content.content == {
            "div": {"p": {"a": {"@href": "http://x", "#text": "the docs"}, "#text": "Read  before shipping."}}
        }

    def test_repeated_siblings_become_a_list_and_lose_their_position(self):
        entry = self._entry(
            extra='<content type="xhtml"><div><p>Intro.</p><h2>Section</h2><p>Body.</p></div></content>'
        )

        assert entry.content.content == {"div": {"p": ["Intro.", "Body."], "h2": "Section"}}

    def test_void_elements_have_no_content(self):
        entry = self._entry(extra='<content type="xhtml"><div><p>line<br/>break</p></div></content>')

        assert entry.content.content == {"div": {"p": {"br": None, "#text": "linebreak"}}}

    def test_inline_markup_without_a_wrapper_element_is_dropped(self):
        """Known Tag limitation, not new: text next to child elements wins and the elements go."""
        entry = self._entry(extra='<content type="xhtml">lead <b>bold</b> trail</content>')

        assert entry.content.content == "lead  trail"

    def test_xhtml_content_round_trips_through_a_dump(self):
        feed = AtomParser.parse(
            FEED_TEMPLATE.format(extra=f"<entry><id>urn:1</id><title>T</title>{self.XHTML_CONTENT}</entry>")
        )
        dumped = feed.model_dump(mode="json")

        assert Atom.model_validate(dumped).model_dump(mode="json") == dumped
        assert json.dumps(feed.dict_plain())

    def test_html_content_stays_escaped_text(self):
        entry = self._entry(extra='<content type="html">&lt;p&gt;Body&lt;/p&gt;</content>')

        assert entry.content.content == "<p>Body</p>"
        assert entry.content.attributes == {"type": "html"}

    def test_content_without_type_is_plain_text(self):
        entry = self._entry(extra="<content>Just text</content>")

        assert entry.content.content == "Just text"
        assert entry.content.attributes == {}

    def test_empty_xhtml_construct_is_none(self):
        """A self-closing text construct still has no content, only its attributes."""
        entry = self._entry(extra='<content type="xhtml"/>')

        assert entry.content.content is None
        assert entry.content.attributes == {"type": "xhtml"}


class TestNamespacePrefixedRoot:
    """A valid Atom document may bind the Atom namespace to a prefix instead of the default one."""

    PREFIXED = """<?xml version="1.0" encoding="utf-8"?>
<atom:feed xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</atom:id>
  <atom:title>Example Feed</atom:title>
  <atom:updated>2003-12-13T18:30:02Z</atom:updated>
  <atom:link href="http://example.org/"/>
  <atom:entry>
    <atom:id>urn:entry:1</atom:id>
    <atom:title>Atom-Powered Robots Run Amok</atom:title>
  </atom:entry>
  <atom:entry>
    <atom:id>urn:entry:2</atom:id>
    <atom:title>Second Entry</atom:title>
  </atom:entry>
</atom:feed>"""

    def test_prefixed_root_is_unwrapped_and_normalized(self):
        feed = AtomParser.parse(self.PREFIXED).feed.content

        assert feed.id.content == "urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6"
        assert feed.title.content == "Example Feed"
        assert isinstance(feed.updated.content, datetime)
        assert feed.links[0].attributes["href"] == "http://example.org/"

    def test_prefixed_entries_are_normalized(self):
        feed = AtomParser.parse(self.PREFIXED).feed.content

        assert len(feed.entries) == 2
        assert isinstance(feed.entries[0].content, Entry)
        assert feed.entries[0].content.title.content == "Atom-Powered Robots Run Amok"
        assert feed.entries[1].content.title.content == "Second Entry"

    def test_foreign_namespaces_keep_their_prefix(self):
        data = self.PREFIXED.replace(
            "<atom:entry>",
            '<atom:entry xmlns:media="http://search.yahoo.com/mrss/"><media:thumbnail url="u"/>',
        )
        feed = AtomParser.parse(data).feed.content

        assert feed.entries[0].content.model_extra["media:thumbnail"] == {"@url": "u"}
