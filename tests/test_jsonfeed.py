"""
Unit tests for ``rss_parser.jsonfeed``: the mapper per feed type, every documented fallback,
and the ``JsonFeedReport`` counts. Hand-written minimal fixtures, one decision at a time - the
full-corpus spec conformance suite lives in tests/test_jsonfeed_conformance.py.
"""

import pytest

from rss_parser import AtomParser, JsonFeedReport, PodcastParser, RDFParser, RSSParser, to_json_feed
from rss_parser.models import XMLBaseModel

RSS_HEADER = '<rss version="2.0"><channel><title>T</title><link>http://example.com</link><description>D</description>'
RSS_FOOTER = "</channel></rss>"

ATOM_HEADER = '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:feed</id><title>T</title>'
ATOM_FOOTER = "</feed>"

RDF_HEADER = """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel rdf:about="http://example.com/"><title>T</title><link>http://example.com</link>
<description>D</description></channel>"""
RDF_FOOTER = "</rdf:RDF>"


def rss(item_xml: str) -> str:
    return f"{RSS_HEADER}{item_xml}{RSS_FOOTER}"


def atom(entry_xml: str) -> str:
    return f"{ATOM_HEADER}{entry_xml}{ATOM_FOOTER}"


def rdf(item_xml: str) -> str:
    return f"{RDF_HEADER}{item_xml}{RDF_FOOTER}"


class _NotAFeed(XMLBaseModel):
    """Not an RSS/Atom/RDF instance - to_json_feed must not fabricate a mapping for it."""


class TestReturnShape:
    def test_returns_a_dict_and_a_report(self):
        feed = RSSParser.parse(rss("<item><title>One</title></item>"))
        document, report = to_json_feed(feed)
        assert isinstance(document, dict)
        assert isinstance(report, JsonFeedReport)

    def test_document_has_the_required_top_level_fields(self):
        feed = RSSParser.parse(rss("<item><title>One</title></item>"))
        document, _ = to_json_feed(feed)
        assert document["version"] == "https://jsonfeed.org/version/1.1"
        assert document["title"] == "T"
        assert "items" in document

    def test_unsupported_model_raises_type_error(self):
        with pytest.raises(TypeError):
            to_json_feed(_NotAFeed())


class TestRSSItemId:
    def test_guid_wins_over_link(self):
        feed = RSSParser.parse(rss("<item><title>One</title><guid>g</guid><link>http://example.com/1</link></item>"))
        document, report = to_json_feed(feed)
        assert document["items"][0]["id"] == "g"
        assert report.dropped_items == 0

    def test_falls_back_to_the_first_link(self):
        feed = RSSParser.parse(rss("<item><title>One</title><link>http://example.com/1</link></item>"))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["id"] == "http://example.com/1"

    def test_no_guid_and_no_link_is_dropped_and_counted(self):
        feed = RSSParser.parse(rss("<item><description>Only a description</description></item>"))
        document, report = to_json_feed(feed)
        assert document["items"] == []
        assert report.dropped_items == 1

    def test_id_is_never_synthesized_from_content(self):
        """No title/content-derived id, even though the item clearly has content."""
        feed = RSSParser.parse(rss("<item><title>Has a title but nothing else</title></item>"))
        _, report = to_json_feed(feed)
        assert report.dropped_items == 1


class TestRSSContent:
    def test_description_becomes_content_html(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><description>&lt;p&gt;hi&lt;/p&gt;</description></item>"))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_html"] == "<p>hi</p>"
        assert "content_text" not in document["items"][0]

    def test_no_description_gets_empty_content_text(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>Title only</title></item>"))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_text"] == ""
        assert "content_html" not in document["items"][0]


class TestRSSAuthorsAndTags:
    def test_author_email_goes_in_name(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>X</title><author>a@example.com</author></item>"))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["authors"] == [{"name": "a@example.com"}]

    def test_no_author_omits_the_field(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>X</title></item>"))
        document, _ = to_json_feed(feed)
        assert "authors" not in document["items"][0]

    def test_category_domain_attribute_is_dropped(self):
        feed = RSSParser.parse(rss('<item><guid>g</guid><title>X</title><category domain="d">News</category></item>'))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["tags"] == ["News"]


class TestRSSAttachments:
    def test_enclosure_with_url_and_type_is_kept(self):
        enclosure = '<enclosure url="http://x/a.mp3" type="audio/mpeg" length="10"/>'
        feed = RSSParser.parse(rss(f"<item><guid>g</guid><title>X</title>{enclosure}</item>"))
        document, report = to_json_feed(feed)
        assert document["items"][0]["attachments"] == [
            {"url": "http://x/a.mp3", "mime_type": "audio/mpeg", "size_in_bytes": 10}
        ]
        assert report.dropped_attachments == 0

    def test_empty_length_is_never_int_cast(self):
        enclosure = '<enclosure url="http://x/a.png" type="image/png" length=""/>'
        feed = RSSParser.parse(rss(f"<item><guid>g</guid><title>X</title>{enclosure}</item>"))
        document, report = to_json_feed(feed)
        attachment = document["items"][0]["attachments"][0]
        assert "size_in_bytes" not in attachment
        assert report.dropped_attachments == 0

    def test_missing_type_drops_the_attachment_and_counts_it(self):
        feed = RSSParser.parse(rss('<item><guid>g</guid><title>X</title><enclosure url="http://x/a.mp3"/></item>'))
        document, report = to_json_feed(feed)
        assert "attachments" not in document["items"][0]
        assert report.dropped_attachments == 1

    def test_missing_url_drops_the_attachment_and_counts_it(self):
        feed = RSSParser.parse(rss('<item><guid>g</guid><title>X</title><enclosure type="audio/mpeg"/></item>'))
        document, report = to_json_feed(feed)
        assert "attachments" not in document["items"][0]
        assert report.dropped_attachments == 1


class TestRSSDates:
    def test_a_parseable_pub_date_is_emitted(self):
        feed = RSSParser.parse(
            rss("<item><guid>g</guid><title>X</title><pubDate>Tue, 19 Oct 2004 13:38:55 -0400</pubDate></item>")
        )
        document, report = to_json_feed(feed)
        assert document["items"][0]["date_published"] == "2004-10-19T13:38:55-04:00"
        assert report.unparsed_dates == 0

    def test_an_unparseable_pub_date_is_omitted_and_counted(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>X</title><pubDate>not a date</pubDate></item>"))
        document, report = to_json_feed(feed)
        assert "date_published" not in document["items"][0]
        assert report.unparsed_dates == 1

    def test_rss_items_never_have_date_modified(self):
        feed = RSSParser.parse(
            rss("<item><guid>g</guid><title>X</title><pubDate>Tue, 19 Oct 2004 13:38:55 -0400</pubDate></item>")
        )
        document, _ = to_json_feed(feed)
        assert "date_modified" not in document["items"][0]


class TestRSSFeedMetadata:
    def test_home_page_url_language_and_description(self):
        feed = RSSParser.parse(
            '<rss version="2.0"><channel><title>T</title><link>http://example.com</link>'
            "<description>D</description><language>en-us</language></channel></rss>"
        )
        document, _ = to_json_feed(feed)
        assert document["home_page_url"] == "http://example.com"
        assert document["description"] == "D"
        assert document["language"] == "en-us"

    def test_self_closing_channel_yields_an_empty_but_valid_document(self):
        feed = RSSParser.parse('<rss version="2.0"><channel/></rss>')
        document, report = to_json_feed(feed)
        assert document["title"] == ""
        assert document["items"] == []
        assert report == JsonFeedReport(0, 0, 0)


class TestPodcastIsHandledAsRSS:
    def test_podcast_maps_through_the_rss_branch_and_drops_itunes_fields(self):
        feed = PodcastParser.parse(
            '<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">'
            "<channel><title>T</title><link>http://example.com</link><description>D</description>"
            "<itunes:author>Someone</itunes:author>"
            "<item><guid>g</guid><title>Ep</title><itunes:duration>100</itunes:duration></item>"
            "</channel></rss>"
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["id"] == "g"
        blob = str(document)
        assert "itunes" not in blob
        assert "_itunes" not in blob


class TestAtomContentRouting:
    def test_absent_type_is_content_text(self):
        feed = AtomParser.parse(atom("<entry><id>u:1</id><title>E</title><content>plain</content></entry>"))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_text"] == "plain"

    def test_type_html_is_content_html(self):
        feed = AtomParser.parse(
            atom('<entry><id>u:1</id><title>E</title><content type="html">&lt;b&gt;hi&lt;/b&gt;</content></entry>')
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_html"] == "<b>hi</b>"

    def test_xhtml_content_falls_back_to_html_summary(self):
        feed = AtomParser.parse(
            atom(
                "<entry><id>u:1</id><title>E</title>"
                '<content type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml"><p>hi</p></div></content>'
                '<summary type="html">&lt;p&gt;fallback&lt;/p&gt;</summary></entry>'
            )
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_html"] == "<p>fallback</p>"
        assert "summary" not in document["items"][0]

    def test_xhtml_content_and_xhtml_summary_gives_empty_content_text(self):
        feed = AtomParser.parse(
            atom(
                "<entry><id>u:1</id><title>E</title>"
                '<content type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml"><p>hi</p></div></content>'
                '<summary type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml"><p>also</p></div></summary>'
                "</entry>"
            )
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_text"] == ""

    def test_no_content_and_no_summary_gives_empty_content_text(self):
        feed = AtomParser.parse(atom("<entry><id>u:1</id><title>E</title></entry>"))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_text"] == ""

    def test_content_and_summary_both_present_summary_is_reported_separately(self):
        feed = AtomParser.parse(
            atom(
                "<entry><id>u:1</id><title>E</title>"
                '<content type="html">&lt;p&gt;full&lt;/p&gt;</content>'
                "<summary>short summary</summary></entry>"
            )
        )
        document, _ = to_json_feed(feed)
        item = document["items"][0]
        assert item["content_html"] == "<p>full</p>"
        assert item["summary"] == "short summary"


class TestAtomIdAndUrl:
    def test_missing_id_is_dropped_and_counted(self):
        feed = AtomParser.parse(atom("<entry><id></id><title>E</title></entry>"))
        _, report = to_json_feed(feed)
        assert report.dropped_items == 1

    def test_item_url_uses_the_alternate_link_not_the_first_link(self):
        feed = AtomParser.parse(
            atom(
                "<entry><id>u:1</id><title>E</title>"
                '<link rel="self" href="http://example.com/self"/>'
                '<link rel="alternate" href="http://example.com/alt"/></entry>'
            )
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["url"] == "http://example.com/alt"

    def test_only_a_self_link_omits_url(self):
        feed = AtomParser.parse(
            atom('<entry><id>u:1</id><title>E</title><link rel="self" href="http://example.com/self"/></entry>')
        )
        document, _ = to_json_feed(feed)
        assert "url" not in document["items"][0]


class TestAtomAuthorsAndTags:
    def test_person_name_and_uri(self):
        feed = AtomParser.parse(
            atom(
                "<entry><id>u:1</id><title>E</title>"
                "<author><name>Jane</name><uri>http://example.com/jane</uri></author></entry>"
            )
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["authors"] == [{"name": "Jane", "url": "http://example.com/jane"}]

    def test_category_term_attribute(self):
        feed = AtomParser.parse(atom('<entry><id>u:1</id><title>E</title><category term="News"/></entry>'))
        document, _ = to_json_feed(feed)
        assert document["items"][0]["tags"] == ["News"]


class TestAtomAttachments:
    def test_rel_enclosure_link_is_an_attachment(self):
        feed = AtomParser.parse(
            atom(
                "<entry><id>u:1</id><title>E</title>"
                '<link rel="enclosure" type="audio/mpeg" length="1337" href="http://x/a.mp3"/></entry>'
            )
        )
        document, report = to_json_feed(feed)
        assert document["items"][0]["attachments"] == [
            {"url": "http://x/a.mp3", "mime_type": "audio/mpeg", "size_in_bytes": 1337}
        ]
        assert report.dropped_attachments == 0

    def test_rel_enclosure_missing_type_is_dropped_and_counted(self):
        feed = AtomParser.parse(
            atom('<entry><id>u:1</id><title>E</title><link rel="enclosure" href="http://x/a.mp3"/></entry>')
        )
        document, report = to_json_feed(feed)
        assert "attachments" not in document["items"][0]
        assert report.dropped_attachments == 1

    def test_non_enclosure_links_are_not_attachments(self):
        feed = AtomParser.parse(
            atom('<entry><id>u:1</id><title>E</title><link rel="alternate" href="http://x/a"/></entry>')
        )
        document, report = to_json_feed(feed)
        assert "attachments" not in document["items"][0]
        assert report.dropped_attachments == 0


class TestAtomFeedMetadata:
    def test_home_page_url_uses_alternate_never_first_link(self):
        feed = AtomParser.parse(
            '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:feed</id><title>T</title>'
            '<link rel="self" href="http://example.com/self"/>'
            '<link rel="alternate" href="http://example.com/alt"/></feed>'
        )
        document, _ = to_json_feed(feed)
        assert document["home_page_url"] == "http://example.com/alt"

    def test_only_self_link_omits_home_page_url(self):
        feed = AtomParser.parse(
            '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:feed</id><title>T</title>'
            '<link rel="self" href="http://example.com/self"/></feed>'
        )
        document, _ = to_json_feed(feed)
        assert "home_page_url" not in document

    def test_language_comes_from_xml_lang_attribute(self):
        feed = AtomParser.parse(
            '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en"><id>urn:feed</id><title>T</title></feed>'
        )
        document, _ = to_json_feed(feed)
        assert document["language"] == "en"

    def test_no_xml_lang_omits_language(self):
        feed = AtomParser.parse('<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:feed</id><title>T</title></feed>')
        document, _ = to_json_feed(feed)
        assert "language" not in document

    def test_subtitle_becomes_description(self):
        feed = AtomParser.parse(
            '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:feed</id><title>T</title>'
            "<subtitle>Sub</subtitle></feed>"
        )
        document, _ = to_json_feed(feed)
        assert document["description"] == "Sub"


class TestRDF:
    def test_rdf_about_is_the_id(self):
        feed = RDFParser.parse(
            rdf('<item rdf:about="http://example.com/1"><title>I</title><link>http://example.com/1</link></item>')
        )
        document, report = to_json_feed(feed)
        assert document["items"][0]["id"] == "http://example.com/1"
        assert report.dropped_items == 0

    def test_description_becomes_content_html(self):
        feed = RDFParser.parse(
            rdf(
                '<item rdf:about="http://example.com/1"><title>I</title><link>http://example.com/1</link>'
                "<description>hi</description></item>"
            )
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_html"] == "hi"

    def test_no_description_gets_empty_content_text(self):
        feed = RDFParser.parse(
            rdf('<item rdf:about="http://example.com/1"><title>I</title><link>http://example.com/1</link></item>')
        )
        document, _ = to_json_feed(feed)
        assert document["items"][0]["content_text"] == ""

    def test_dc_date_is_parsed_via_the_shared_date_validator(self):
        feed = RDFParser.parse(
            rdf(
                '<item rdf:about="http://example.com/1"><title>I</title><link>http://example.com/1</link>'
                "<dc:date>2024-01-02T03:04:05+00:00</dc:date></item>"
            )
        )
        document, report = to_json_feed(feed)
        assert document["items"][0]["date_published"] == "2024-01-02T03:04:05+00:00"
        assert report.unparsed_dates == 0

    def test_unparseable_dc_date_is_omitted_and_counted(self):
        feed = RDFParser.parse(
            rdf(
                '<item rdf:about="http://example.com/1"><title>I</title><link>http://example.com/1</link>'
                "<dc:date>not a date</dc:date></item>"
            )
        )
        document, report = to_json_feed(feed)
        assert "date_published" not in document["items"][0]
        assert report.unparsed_dates == 1

    def test_channel_dc_language(self):
        feed = RDFParser.parse("""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel rdf:about="http://example.com/"><title>T</title><link>http://example.com</link>
<description>D</description><dc:language>en-us</dc:language></channel>
</rdf:RDF>""")
        document, _ = to_json_feed(feed)
        assert document["language"] == "en-us"

    def test_no_channel_dc_language_omits_language(self):
        feed = RDFParser.parse(rdf(""))
        document, _ = to_json_feed(feed)
        assert "language" not in document


class TestFeedUrl:
    def test_omitted_by_default(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>X</title></item>"))
        document, _ = to_json_feed(feed)
        assert "feed_url" not in document

    def test_set_when_passed(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>X</title></item>"))
        document, _ = to_json_feed(feed, feed_url="https://example.com/feed.xml")
        assert document["feed_url"] == "https://example.com/feed.xml"


class TestSelfClosingWrappers:
    """A self-closing wrapper tag (<item/>, <entry/>, <feed/>, <channel/>) has no content at
    all - that is an empty container, not an id-less item, so it must not be counted as dropped.
    """

    def test_self_closing_rss_item_is_skipped_without_being_counted(self):
        feed = RSSParser.parse(rss("<item/>"))
        document, report = to_json_feed(feed)
        assert document["items"] == []
        assert report.dropped_items == 0

    def test_self_closing_atom_entry_is_skipped_without_being_counted(self):
        feed = AtomParser.parse(atom("<entry/>"))
        document, report = to_json_feed(feed)
        assert document["items"] == []
        assert report.dropped_items == 0

    def test_self_closing_atom_author_is_ignored(self):
        feed = AtomParser.parse(atom("<entry><id>u:1</id><title>E</title><author/></entry>"))
        document, _ = to_json_feed(feed)
        assert "authors" not in document["items"][0]

    def test_self_closing_atom_feed_yields_an_empty_document(self):
        feed = AtomParser.parse('<feed xmlns="http://www.w3.org/2005/Atom"/>')
        document, report = to_json_feed(feed)
        assert document["items"] == []
        assert document["title"] == ""
        assert report == JsonFeedReport(0, 0, 0)

    def test_self_closing_rdf_channel_yields_an_empty_but_valid_document(self):
        feed = RDFParser.parse(
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns="http://purl.org/rss/1.0/"><channel/></rdf:RDF>'
        )
        document, report = to_json_feed(feed)
        assert document["items"] == []
        assert document["title"] == ""
        assert report == JsonFeedReport(0, 0, 0)


class TestRDFItemIdFallback:
    def test_falls_back_to_link_when_rdf_about_is_absent(self):
        feed = RDFParser.parse(rdf("<item><title>I</title><link>http://example.com/1</link></item>"))
        document, report = to_json_feed(feed)
        assert document["items"][0]["id"] == "http://example.com/1"
        assert report.dropped_items == 0

    def test_dropped_when_neither_rdf_about_nor_link_content_is_present(self):
        feed = RDFParser.parse(rdf("<item><title>I</title><link/></item>"))
        _, report = to_json_feed(feed)
        assert report.dropped_items == 1


class TestDublinCore:
    """dc:creator carries the byline on Slashdot, Hacker News and NPR; dc:subject categorises RSS 1.0."""

    def test_rss_dc_creator_is_used_when_there_is_no_author(self):
        feed = RSSParser.parse(rss("<item><guid>g</guid><title>I</title><dc:creator>BeauHD</dc:creator></item>"))

        (item,) = to_json_feed(feed)[0]["items"]

        assert item["authors"] == [{"name": "BeauHD"}]

    def test_rss_author_element_wins_over_dc_creator(self):
        feed = RSSParser.parse(
            rss("<item><guid>g</guid><title>I</title><author>a@x.com</author><dc:creator>Other</dc:creator></item>")
        )

        (item,) = to_json_feed(feed)[0]["items"]

        assert item["authors"] == [{"name": "a@x.com"}]

    def test_rdf_dc_creator_becomes_an_author(self):
        feed = RDFParser.parse(
            rdf("<item><title>I</title><link>http://x/1</link><dc:creator>BeauHD</dc:creator></item>")
        )

        (item,) = to_json_feed(feed)[0]["items"]

        assert item["authors"] == [{"name": "BeauHD"}]

    def test_rdf_single_dc_subject_becomes_one_tag(self):
        feed = RDFParser.parse(
            rdf("<item><title>I</title><link>http://x/1</link><dc:subject>transportation</dc:subject></item>")
        )

        (item,) = to_json_feed(feed)[0]["items"]

        assert item["tags"] == ["transportation"]

    def test_rdf_repeated_dc_subject_becomes_a_list_of_tags(self):
        feed = RDFParser.parse(
            rdf(
                "<item><title>I</title><link>http://x/1</link>"
                "<dc:subject>news</dc:subject><dc:subject>tech</dc:subject></item>"
            )
        )

        (item,) = to_json_feed(feed)[0]["items"]

        assert item["tags"] == ["news", "tech"]

    def test_a_structured_dc_value_is_ignored_rather_than_guessed_at(self):
        """Dublin Core terms can carry rdf:resource attributes, which are not a name or a tag."""
        feed = RDFParser.parse(
            rdf(
                "<item><title>I</title><link>http://x/1</link>"
                '<dc:creator rdf:resource="http://x/people/1"/><dc:subject rdf:resource="http://x/t/1"/></item>'
            )
        )

        (item,) = to_json_feed(feed)[0]["items"]

        assert "authors" not in item
        assert "tags" not in item
