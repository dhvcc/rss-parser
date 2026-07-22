# rss-parser

**Typed, pydantic-powered RSS/Atom parsing for Python.**

[![PyPI version](https://img.shields.io/pypi/v/rss-parser)](https://pypi.org/project/rss-parser)
[![Python versions](https://img.shields.io/pypi/pyversions/rss-parser)](https://pypi.org/project/rss-parser)
[![Downloads](https://pepy.tech/badge/rss-parser)](https://pepy.tech/project/rss-parser)
[![Wheel status](https://img.shields.io/pypi/wheel/rss-parser)](https://pypi.org/project/rss-parser)
[![License](https://img.shields.io/pypi/l/rss-parser?color=success)](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)

![CI](https://github.com/dhvcc/rss-parser/actions/workflows/ci.yml/badge.svg?branch=master)
![Docs](https://github.com/dhvcc/rss-parser/actions/workflows/docs.yml/badge.svg)
![PyPi publish](https://github.com/dhvcc/rss-parser/actions/workflows/publish_to_pypi.yml/badge.svg)

`rss-parser` turns RSS/Atom XML into typed [pydantic](https://docs.pydantic.dev) models —
autocomplete, validation, and clear errors instead of digging through nested dicts.

**[Documentation](https://dhvcc.github.io/rss-parser)**

## Installation

```bash
pip install rss-parser
```

## Quickstart

```python
from rss_parser import parse
from requests import get  # noqa

rss_url = "https://rss.art19.com/apology-line"
response = get(rss_url)

feed = parse(response.text)  # detects RSS 2.0 / 0.9x, Atom 1.0 or RSS 1.0 (RDF)

print("Language", feed.channel.language)
print("RSS", feed.version)

for item in feed.channel.items:
    print(item.title)
    print(str(item.description)[:50])

# Language en
# RSS 2.0
# Wondery Presents - Flipping The Bird: Elon vs Twitter
# <p>When Elon Musk posted a video of himself arrivi
# Introducing: The Apology Line
# <p>If you could call a number and say you’re sorry
```

`parse()` picks the right parser from the XML root element and raises `UnknownFeedTypeError`
if the document is not a feed. If you already know the feed type, use the explicit parsers:
`RSSParser`, `AtomParser`, `RDFParser`, `PodcastParser`.

## Podcasts

`itunes:*` tags are supported out of the box, fully typed:

```python
from rss_parser import PodcastParser

podcast = PodcastParser.parse(feed_xml)
channel = podcast.channel.content

channel.itunes_author                    # 'Wondery'
channel.itunes_owner.content.email       # 'iwonder@wondery.com'
channel.itunes_image.attributes["href"]  # artwork url

episode = channel.items[0].content
episode.itunes_duration                  # '00:05:01'
episode.itunes_episode_type              # 'trailer'
```

## Custom fields: one subclass away

The models are generic, so extending the schema doesn't require re-declaring the whole tree:

```python
from typing import Optional
from pydantic import Field

from rss_parser import RSSParser
from rss_parser.models.rss import RSS, Channel, Item
from rss_parser.models.types import Tag


class MyItem(Item):
    dc_creator: Optional[Tag[str]] = Field(alias="dc:creator", default=None)


rss = RSSParser.parse(data, schema=RSS[Channel[MyItem]])

rss.channel.items[0].content.dc_creator
```

And even without a custom schema, unknown tags are never dropped — they're kept in `model_extra`:

```python
rss = RSSParser.parse(podcast_xml)
rss.channel.content.model_extra["itunes:author"]  # 'Wondery'
```

See [Customizing the schema](https://dhvcc.github.io/rss-parser/extending/) for mixins,
repeatable tags, and the field types cheat sheet.

## Migrating from 3.x

4.0 removes the legacy pydantic v1 models, fixes several RSS 2.0 spec violations, and makes the
models generic and lossless. See the
[migration guide](https://dhvcc.github.io/rss-parser/migration/) for the full list.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you
would like to change.

Install dependencies with `poetry install` (`pip install poetry`).

Using `pre-commit` is highly recommended. To install hooks, run:

```bash
poetry run pre-commit install -t=pre-commit -t=pre-push
```

See [Contributing](https://dhvcc.github.io/rss-parser/contributing/) for tests, snapshots, and docs.

## License

[GPLv3](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)
