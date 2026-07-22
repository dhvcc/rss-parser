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


class TestDetectFeedType:
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (RSS_2, FeedType.RSS),
            (RSS_0_91, FeedType.RSS),
            (ATOM, FeedType.ATOM),
            (RDF_1_0, FeedType.RDF),
        ],
        ids=["rss-2.0", "rss-0.91", "atom", "rdf-1.0"],
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
