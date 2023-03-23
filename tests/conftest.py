from datetime import timedelta, timezone, datetime
from pathlib import Path

import pytest

# Get relative path to samples dir no matter the working dir
sample_dir = Path(__file__).parent.resolve() / "samples"


@pytest.fixture
def rss_version_2():
    with open(sample_dir / "rss_2.xml") as f:
        return f.read()


@pytest.fixture
def rss_version_2_data_dict():
    return {
        "language": "en-us",
        "copyright": "Copyright 2004 NotePage, Inc.",
        "managing_editor": "marketing@feedforall.com",
        "web_master": "webmaster@feedforall.com",
        "pub_date": datetime(
            2004, 10, 19, 13, 38, 55, tzinfo=timezone(timedelta(days=-1, seconds=72000))
        ),
        "last_build_date": datetime(
            2004, 10, 19, 13, 39, 14, tzinfo=timezone(timedelta(days=-1, seconds=72000))
        ),
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
            "content": "RSS is a fascinating technology. The uses for RSS are expanding daily. Take a closer look at how various industries are using the benefits of RSS in their businesses.",
            "attributes": {},
        },
    }


@pytest.fixture
def atom_feed():
    with open(sample_dir / "atom.xml") as f:
        return f.read()
