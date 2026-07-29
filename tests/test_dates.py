from datetime import UTC, datetime

from rss_parser import RSSParser
from rss_parser.models.types.date import validate_dt_or_str

ITEM_TEMPLATE = (
    "<rss version='2.0'><channel><title>T</title><link>L</link><description>D</description>"
    "<item><title>t</title><pubDate>{date}</pubDate></item></channel></rss>"
)


def parse_pub_date(date: str):
    rss = RSSParser.parse(ITEM_TEMPLATE.format(date=date))
    return rss.channel.content.items[0].content.pub_date.content


class TestDateParsing:
    def test_rfc_822(self):
        parsed = parse_pub_date("Sat, 07 Sep 2002 00:00:01 GMT")

        assert parsed == datetime(2002, 9, 7, 0, 0, 1, tzinfo=UTC)

    def test_rfc_822_with_two_digit_year(self):
        parsed = parse_pub_date("Sat, 07 Sep 02 00:00:01 GMT")

        assert parsed == datetime(2002, 9, 7, 0, 0, 1, tzinfo=UTC)

    def test_iso_8601(self):
        parsed = parse_pub_date("2002-09-07T00:00:01+00:00")

        assert parsed == datetime(2002, 9, 7, 0, 0, 1, tzinfo=UTC)

    def test_unparseable_date_is_kept_as_string(self):
        """Dates in the wild are too messy to reject a whole feed over one of them."""
        parsed = parse_pub_date("someday, probably")

        assert parsed == "someday, probably"

    def test_datetime_instance_passes_through(self):
        now = datetime(2020, 1, 1, tzinfo=UTC)
        assert validate_dt_or_str(now) is now
