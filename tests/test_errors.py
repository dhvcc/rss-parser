from xml.parsers.expat import ExpatError

import pytest
from pydantic import ValidationError

from rss_parser import (
    AtomParser,
    FeedType,
    InvalidXMLError,
    RSSParser,
    UnknownFeedTypeError,
    detect_feed_type,
    parse,
)


class TestInvalidXML:
    @pytest.mark.parametrize(
        "data",
        ["", "not xml at all", "<rss><channel>unclosed", "<rss></feed>", "\x00\x01"],
        ids=["empty", "plain-text", "unclosed-tag", "mismatched-tag", "binary-junk"],
    )
    def test_malformed_xml_raises_invalid_xml_error(self, data):
        with pytest.raises(InvalidXMLError):
            parse(data)

    def test_original_expat_error_is_chained(self):
        with pytest.raises(InvalidXMLError) as exc_info:
            RSSParser.parse("<rss>")

        assert isinstance(exc_info.value.__cause__, ExpatError)

    def test_detect_feed_type_raises_too(self):
        with pytest.raises(InvalidXMLError):
            detect_feed_type("garbage")

    def test_invalid_xml_error_is_a_value_error(self):
        """Catching ValueError catches every rss-parser error."""
        assert issubclass(InvalidXMLError, ValueError)
        assert issubclass(UnknownFeedTypeError, ValueError)


class TestBytesInput:
    """Feeds arrive from the network as bytes - they must not be stringified."""

    RSS = '<rss version="2.0"><channel><title>T</title><link>L</link><description>D</description></channel></rss>'

    def test_bytes_are_parsed(self):
        assert str(parse(self.RSS.encode()).channel.title) == "T"

    def test_str_and_bytes_agree(self):
        assert parse(self.RSS).model_dump() == parse(self.RSS.encode()).model_dump()

    def test_detect_feed_type_accepts_bytes(self):
        assert detect_feed_type(self.RSS.encode()) is FeedType.RSS

    @pytest.mark.parametrize("encoding", ["utf-8", "windows-1251", "iso-8859-5"])
    def test_declared_encoding_is_honored(self, encoding):
        """The document's own declaration decides - that's why bytes are passed through as-is."""
        xml = (
            f'<?xml version="1.0" encoding="{encoding}"?>'
            f'<rss version="2.0"><channel><title>Привет</title><link>L</link>'
            f"<description>D</description></channel></rss>"
        )

        feed = parse(xml.encode(encoding))

        assert str(feed.channel.title) == "Привет"

    def test_non_utf8_bytes_would_break_if_we_decoded_for_you(self):
        """Guards the reason bytes are not decoded here: guessing UTF-8 raises."""
        xml = (
            '<?xml version="1.0" encoding="windows-1251"?>'
            '<rss version="2.0"><channel><title>Привет</title><link>L</link>'
            "<description>D</description></channel></rss>"
        ).encode("windows-1251")

        with pytest.raises(UnicodeDecodeError):
            xml.decode("utf-8")

        assert str(parse(xml).channel.title) == "Привет"

    def test_malformed_bytes_still_raise_invalid_xml_error(self):
        with pytest.raises(InvalidXMLError):
            parse(b"<rss><channel>unclosed")

    def test_anything_else_is_stringified(self):
        """Objects that render to XML keep working, as they did before bytes were supported."""

        class Readable:
            def __str__(self):
                return TestBytesInput.RSS

        assert str(parse(Readable()).channel.title) == "T"  # type: ignore[arg-type]


class TestEntitiesAreDisabled:
    """xmltodict runs with disable_entities=True - the guarantee documented in SECURITY.md."""

    @staticmethod
    def _feed(doctype: str, title: str) -> str:
        return (
            f'<?xml version="1.0"?>{doctype}'
            f'<rss version="2.0"><channel><title>{title}</title><link>L</link>'
            f"<description>D</description></channel></rss>"
        )

    def test_external_entity_is_refused(self):
        """XXE: a SYSTEM entity must never be resolved."""
        data = self._feed('<!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>', "&xxe;")

        with pytest.raises(ValueError, match="entities are disabled"):
            RSSParser.parse(data)

    def test_entity_expansion_is_refused(self):
        """Billion laughs: expansion is refused at declaration time, before it can blow up."""
        entities = '<!ENTITY a0 "AAAAAAAAAA">' + "".join(
            f'<!ENTITY a{i} "' + f"&a{i - 1};" * 10 + '">' for i in range(1, 5)
        )
        data = self._feed(f"<!DOCTYPE rss [{entities}]>", "&a4;")

        with pytest.raises(ValueError, match="entities are disabled"):
            RSSParser.parse(data)


class TestUnknownFeedType:
    def test_well_formed_non_feed_xml(self):
        with pytest.raises(UnknownFeedTypeError, match="html"):
            parse("<html><body>hi</body></html>")


class TestValidationErrors:
    def test_error_path_points_at_the_broken_element(self):
        with pytest.raises(ValidationError) as exc_info:
            RSSParser.parse("<rss><channel><title>T</title><description>D</description></channel></rss>")

        (error,) = exc_info.value.errors()
        assert error["loc"] == ("channel", "content", "link")
        assert error["type"] == "missing"

    def test_wrong_parser_for_feed_type_fails_with_validation_error(self):
        with pytest.raises(ValidationError):
            AtomParser.parse(
                '<rss version="2.0"><channel><title>T</title><link>L</link>'
                "<description>D</description></channel></rss>"
            )
