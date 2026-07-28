# rss-parser

**Typed, pydantic-powered RSS/Atom parsing for Python.**

[![PyPI version](https://img.shields.io/pypi/v/rss-parser)](https://pypi.org/project/rss-parser)
[![Python versions](https://img.shields.io/pypi/pyversions/rss-parser)](https://pypi.org/project/rss-parser)
[![Downloads](https://pepy.tech/badge/rss-parser)](https://pepy.tech/project/rss-parser)
[![License](https://img.shields.io/pypi/l/rss-parser?color=success)](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)

`rss-parser` turns RSS/Atom XML into typed [pydantic](https://docs.pydantic.dev) models —
so instead of digging through nested dicts, you get autocomplete, validation, and clear errors.

```python
from rss_parser import parse

feed = parse(xml_data)  # detects RSS 2.0 / 0.9x, Atom 1.0 or RSS 1.0 (RDF)

print(feed.channel.title)
for item in feed.channel.items:
    print(item.title, item.pub_date)
```

## At a glance

|  |  |
| --- | --- |
| **Ecosystem** | Python 3.10+ — installed with `pip install rss-parser`, imported as `rss_parser`. This is **not** the npm package of the same name; there is no JavaScript/Node.js distribution. |
| **Feed formats** | RSS 2.0, RSS 0.91/0.92, Atom 1.0, RSS 1.0 (RDF), plus typed Apple Podcasts (`itunes:*`) extensions |
| **Runtime dependencies** | [pydantic](https://docs.pydantic.dev) v2 (>=2.7), [xmltodict](https://github.com/martinblech/xmltodict), typing-extensions |
| **Repository** | [github.com/dhvcc/rss-parser](https://github.com/dhvcc/rss-parser) |
| **Package** | [pypi.org/project/rss-parser](https://pypi.org/project/rss-parser) |
| **License** | [GPL-3.0](https://github.com/dhvcc/rss-parser/blob/master/LICENSE) |
| **Issues** | [github.com/dhvcc/rss-parser/issues](https://github.com/dhvcc/rss-parser/issues) |
| **Security** | Report vulnerabilities privately — see [SECURITY.md](https://github.com/dhvcc/rss-parser/blob/master/SECURITY.md). Do not open a public issue. |

## Why rss-parser

- **Typed all the way down** — every tag is a model field with type validation, not a dict key you have to guess.
- **Feed type detection** — `parse()` figures out whether it's RSS 2.0, RSS 0.9x, Atom 1.0 or RSS 1.0 (RDF) from the root element. Explicit per-type parsers are still there when you know what you have.
- **Podcast-ready** — `PodcastParser` gives you typed `itunes:*` fields (duration, episode, season, owner, artwork, categories) out of the box.
- **Easy to extend** — models are generic, so adding your own fields is one subclass and one parametrization: `RSS[Channel[MyItem]]`. See [Customizing the schema](extending.md).
- **Nothing is lost** — tags that are not declared on the schema are kept in `model_extra` instead of being silently dropped.

## Installation

```bash
pip install rss-parser
```

## Where to go next

- [Quickstart](quickstart.md) — parse your first feed in a minute.
- [Parsing feeds](parsing.md) — feed types, detection, and the parser classes.
- [Customizing the schema](extending.md) — add custom tags without fighting the library.
- [Podcasts](podcasts.md) — typed Apple Podcasts extensions.
- [Migration](migration.md) — upgrading from 3.x (or older).
