import pytest

from rss_parser import FeedType, PodcastParser, UnknownFeedTypeError, detect_feed_type, parse
from rss_parser.models.atom import Atom
from rss_parser.models.rdf import RDF
from rss_parser.models.rss import RSS
from rss_parser.models.rss.itunes import Podcast
from tests.conftest import SAMPLES_DIR

RSS_2 = (SAMPLES_DIR / "rss" / "rss_2" / "data.xml").read_text(encoding="utf-8")
RSS_0_91 = (SAMPLES_DIR / "rss" / "rss_0_91" / "data.xml").read_text(encoding="utf-8")
ATOM = (SAMPLES_DIR / "atom" / "atom" / "data.xml").read_text(encoding="utf-8")
RDF_1_0 = (SAMPLES_DIR / "rdf" / "rdf_1_0" / "data.xml").read_text(encoding="utf-8")

ATOM_NAMESPACED = """<?xml version="1.0" encoding="utf-8"?>
<atom:feed xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</atom:id>
  <atom:title>Example Feed</atom:title>
  <atom:updated>2003-12-13T18:30:02Z</atom:updated>
  <atom:link href="http://example.org/"/>
  <atom:entry>
    <atom:id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</atom:id>
    <atom:title>Atom-Powered Robots Run Amok</atom:title>
    <atom:updated>2003-12-13T18:30:02Z</atom:updated>
  </atom:entry>
</atom:feed>"""


class TestDetectFeedType:
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (RSS_2, FeedType.RSS),
            (RSS_0_91, FeedType.RSS),
            (ATOM, FeedType.ATOM),
            (ATOM_NAMESPACED, FeedType.ATOM),
            (RDF_1_0, FeedType.RDF),
        ],
        ids=["rss-2.0", "rss-0.91", "atom", "atom-namespaced", "rdf-1.0"],
    )
    def test_detects_feed_type(self, data, expected):
        assert detect_feed_type(data) == expected

    def test_unknown_root_raises(self):
        with pytest.raises(UnknownFeedTypeError, match="html"):
            detect_feed_type("<html><body>not a feed</body></html>")


class TestUniversalParse:
    def test_rss_2(self):
        feed = parse(RSS_2)

        assert isinstance(feed, RSS)
        assert feed.version.content == "2.0"

    def test_rss_0_91(self):
        feed = parse(RSS_0_91)

        assert isinstance(feed, RSS)
        assert feed.version.content == "0.91"

    def test_atom(self):
        feed = parse(ATOM)

        assert isinstance(feed, Atom)

    def test_atom_with_namespace_prefixed_root(self):
        feed = parse(ATOM_NAMESPACED)

        assert isinstance(feed, Atom)
        assert feed.feed.content.title.content == "Example Feed"
        assert len(feed.feed.content.entries) == 1
        assert feed.feed.content.entries[0].content.title.content == "Atom-Powered Robots Run Amok"

    def test_rdf(self):
        feed = parse(RDF_1_0)

        assert isinstance(feed, RDF)
        assert feed.channel.content.title.content == "Meerkat"
        assert len(feed.items) == 2

    def test_unknown_root_raises_with_supported_types_listed(self):
        with pytest.raises(UnknownFeedTypeError, match="rdf:RDF"):
            parse("<html><body>not a feed</body></html>")

    def test_parser_override(self):
        feed = parse(RSS_2, parsers={FeedType.RSS: PodcastParser})

        assert isinstance(feed, Podcast)
