"""
Real-world feed corpus tests.

Feeds in tests/corpus/ were captured from the wild; every expect.json was written by
inspecting the raw XML (see tests/corpus/README.md), so the parser is checked against
the documents themselves, not against its own output.
"""

import json
import re
from pathlib import Path

import pytest

from rss_parser import FeedType, PodcastParser, detect_feed_type, parse
from rss_parser.models.atom import Atom
from rss_parser.models.rdf import RDF
from rss_parser.models.rss import RSS
from tests.conftest import iter_corpus

MODEL_BY_TYPE = {"rss": RSS, "atom": Atom, "rdf": RDF}
FEED_TYPE_BY_TYPE = {"rss": FeedType.RSS, "atom": FeedType.ATOM, "rdf": FeedType.RDF}


def load_feed(feed_dir: Path, expect: dict) -> str:
    return (feed_dir / "data.xml").read_bytes().decode(expect.get("encoding", "utf-8"))


def get_items(feed):
    if isinstance(feed, RSS):
        return feed.channel.content.items
    if isinstance(feed, Atom):
        return feed.feed.content.entries
    return feed.items


CORPUS = list(iter_corpus())
CORPUS_IDS = [f"{kind}/{feed_dir.name}" for kind, feed_dir in CORPUS]


@pytest.mark.parametrize(("kind", "feed_dir"), CORPUS, ids=CORPUS_IDS)
def test_corpus_feed(kind, feed_dir):
    expect = json.loads((feed_dir / "expect.json").read_text(encoding="utf-8"))
    data = load_feed(feed_dir, expect)

    # Detection matches the root element of the document
    assert detect_feed_type(data) == FEED_TYPE_BY_TYPE[expect["type"]]

    feed = parse(data)
    assert isinstance(feed, MODEL_BY_TYPE[expect["type"]])

    if "version" in expect:
        assert feed.version.content == expect["version"]

    # Facts derived from the raw XML
    channel = feed.channel.content if hasattr(feed, "channel") else feed.feed.content
    assert str(channel.title) == expect["title"]

    items = get_items(feed)
    assert len(items) == expect["items"]
    assert str(items[0].content.title) == expect["first_item_title"]


@pytest.mark.parametrize(("kind", "feed_dir"), CORPUS, ids=CORPUS_IDS)
def test_corpus_feed_serializes(kind, feed_dir):
    """Every corpus feed must survive both serialization paths."""
    expect = json.loads((feed_dir / "expect.json").read_text(encoding="utf-8"))
    feed = parse(load_feed(feed_dir, expect))

    assert json.loads(feed.model_dump_json())
    assert json.loads(feed.json_plain())


@pytest.mark.parametrize(
    ("kind", "feed_dir"),
    [(kind, feed_dir) for kind, feed_dir in CORPUS if kind == "podcast"],
    ids=[i for i in CORPUS_IDS if i.startswith("podcast/")],
)
def test_corpus_podcast_itunes_fields(kind, feed_dir):
    expect = json.loads((feed_dir / "expect.json").read_text(encoding="utf-8"))
    podcast = PodcastParser.parse(load_feed(feed_dir, expect))

    assert str(podcast.channel.content.itunes_author) == expect["itunes_author"]


def test_corpus_expectations_are_complete():
    """Every corpus feed dir must carry a reviewed expect.json with the required facts."""
    assert CORPUS, "corpus is empty"
    for _, feed_dir in CORPUS:
        expect = json.loads((feed_dir / "expect.json").read_text(encoding="utf-8"))
        missing = {"type", "title", "items", "first_item_title"} - set(expect)
        assert not missing, f"{feed_dir} expect.json is missing {missing}"


def test_corpus_titles_match_raw_xml():
    """Cross-check: the expected channel title literally appears in the raw document."""
    for _, feed_dir in CORPUS:
        expect = json.loads((feed_dir / "expect.json").read_text(encoding="utf-8"))
        raw = load_feed(feed_dir, expect)
        # Titles may be entity-encoded in the XML; normalize apostrophes and ampersands
        pattern = re.escape(expect["title"]).replace("'", "(?:'|&apos;|&#0?39;)").replace("&", "(?:&|&amp;)")
        assert re.search(pattern, raw), f"{feed_dir}: expected title not found in raw XML"
