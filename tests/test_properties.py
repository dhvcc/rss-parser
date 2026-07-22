"""
Property-based tests: invariants that must hold for *any* feed, not just the ones we thought of.
"""

from xml.sax.saxutils import escape

from hypothesis import given, settings
from hypothesis import strategies as st

from rss_parser import RSSParser
from rss_parser.models.rss import RSS

# XML 1.0 can't carry control characters, and xmltodict strips surrounding whitespace,
# so generate stripped, control-free, non-empty text.
xml_text = (
    st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1, max_size=50)
    .map(str.strip)
    .filter(bool)
)

tag_names = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10)


def render_rss(channel_title, item_titles, extra_channel_xml=""):
    items = "".join(f"<item><title>{escape(t)}</title></item>" for t in item_titles)
    return (
        f'<rss version="2.0"><channel>'
        f"<title>{escape(channel_title)}</title>"
        f"<link>http://example.com</link>"
        f"<description>D</description>"
        f"{extra_channel_xml}{items}"
        f"</channel></rss>"
    )


@settings(max_examples=50)
@given(channel_title=xml_text, item_titles=st.lists(xml_text, min_size=0, max_size=5))
def test_text_content_round_trips(channel_title, item_titles):
    """Any escaped text placed in a tag comes back out unchanged."""
    rss = RSSParser.parse(render_rss(channel_title, item_titles))

    assert rss.channel.content.title.content == channel_title
    assert [item.content.title.content for item in rss.channel.content.items] == item_titles


@settings(max_examples=50)
@given(count=st.integers(min_value=0, max_value=5))
def test_items_are_always_a_list(count):
    """The xmltodict one-element-isn't-a-list quirk must never leak through."""
    rss = RSSParser.parse(render_rss("T", [f"item {i}" for i in range(count)]))

    items = rss.channel.content.items
    assert isinstance(items, list)
    assert len(items) == count


@settings(max_examples=50)
@given(name=tag_names, value=xml_text)
def test_unknown_namespaced_tags_are_never_dropped(name, value):
    key = f"x:{name}"
    rss = RSSParser.parse(render_rss("T", [], f"<{key}>{escape(value)}</{key}>"))

    assert rss.channel.content.model_extra[key] == value


@settings(max_examples=50)
@given(channel_title=xml_text, item_titles=st.lists(xml_text, min_size=1, max_size=3))
def test_dump_validate_round_trip_is_idempotent(channel_title, item_titles):
    """model_validate(model_dump()) must reproduce the exact same model."""
    rss = RSSParser.parse(render_rss(channel_title, item_titles))

    assert RSS.model_validate(rss.model_dump()) == rss


@settings(max_examples=50)
@given(value=xml_text)
def test_attributes_survive(value):
    rss = RSSParser.parse(render_rss("T", [], f'<category someAttr="{escape(value, {chr(34): "&quot;"})}"/>'))

    assert rss.channel.content.categories[0].attributes == {"some_attr": value}
