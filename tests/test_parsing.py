from datetime import datetime, timedelta, timezone

import pytest

from rss_parser import Parser


@pytest.mark.parametrize("sample", [["rss_2.xml"]], indirect=True)
def test_parses_rss_version_2(sample):
    # Expect basic RSSv2 to be parsed
    parser = Parser(xml=sample)
    rss = parser.parse()

    assert rss
    assert rss.dict() == {
        "version": "2.0",
        "channel": {
            "language": "en-us",
            "copyright": "Copyright 2004 NotePage, Inc.",
            "items": [],
            "managing_editor": "marketing@feedforall.com",
            "web_master": "webmaster@feedforall.com",
            "pub_date": datetime(2004, 10, 19, 13, 38, 55, tzinfo=timezone(timedelta(days=-1, seconds=72000))),
            "last_build_date": datetime(2004, 10, 19, 13, 39, 14, tzinfo=timezone(timedelta(days=-1, seconds=72000))),
            "category": {
                "content": "Computers/Software/Internet/Site Management/Content Management",
                "attributes": {"@domain": "www.dmoz.com"},
            },
            "generator": "FeedForAll Beta1 (0.0.1.8)",
            "docs": "http://blogs.law.harvard.edu/tech/rss",
            "cloud": None,
            "ttl": None,
            "image": {
                "url": "http://www.feedforall.com/ffalogo48x48.gif",
                "title": "FeedForAll Sample Feed",
                "link": "http://www.feedforall.com/industry-solutions.htm",
                "width": 48,
                "height": 48,
                "description": "FeedForAll Sample Feed",
            },
            "rating": None,
            "text_input": None,
            "skip_hours": None,
            "skip_days": None,
            "title": "FeedForAll Sample Feed",
            "link": "http://www.feedforall.com/industry-solutions.htm",
            "description": {
                "content": "RSS is a fascinating technology. The uses for RSS are expanding daily. "
                "Take a closer look at how various industries are using the benefits of RSS in their businesses.",
                "attributes": {},
            },
        },
    }


def test_parses_rss_version_2_category_no_attr(rss_version_2_no_attr_category, rss_version_2_data_dict):
    # Expect basic RSSv2 to be parsed
    parser = Parser(xml=rss_version_2_no_attr_category)
    rss = parser.parse()
    expected = rss_version_2_data_dict
    expected["channel"]["category"] = {
        "content": "Computers/Software/Internet/Site Management/Content Management",
        "attributes": {},
    }

    assert rss
    assert rss.dict() == expected


def test_fails_atom_feed(atom_feed):
    # Expect ATOM feed to fail since it's not supported
    parser = Parser(xml=atom_feed)

    with pytest.raises(NotImplementedError):
        parser.parse()
