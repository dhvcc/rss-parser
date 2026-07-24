from xml.parsers.expat import ExpatError

import pytest
from pydantic import ValidationError

from rss_parser import (
    AtomParser,
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
