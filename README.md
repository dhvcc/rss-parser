# Rss parser

[![Downloads](https://pepy.tech/badge/rss-parser)](https://pepy.tech/project/rss-parser)
[![Downloads](https://pepy.tech/badge/rss-parser/month)](https://pepy.tech/project/rss-parser/month)
[![Downloads](https://pepy.tech/badge/rss-parser/week)](https://pepy.tech/project/rss-parser/week)

[![PyPI version](https://img.shields.io/pypi/v/rss-parser)](https://pypi.org/project/rss-parser)
[![Python versions](https://img.shields.io/pypi/pyversions/rss-parser)](https://pypi.org/project/rss-parser)
[![Wheel status](https://img.shields.io/pypi/wheel/rss-parser)](https://pypi.org/project/rss-parser)
[![License](https://img.shields.io/pypi/l/rss-parser?color=success)](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)
[![GitHub Pages](https://badgen.net/github/status/dhvcc/rss-parser/gh-pages?label=docs)](https://dhvcc.github.io/rss-parser#documentation)

[![Pypi publish](https://github.com/dhvcc/rss-parser/workflows/Pypi%20publish/badge.svg)](https://github.com/dhvcc/rss-parser/actions?query=workflow%3A%22Pypi+publish%22)

# About

`rss-parser` is typed python RSS parsing module built using `BeautifulSoup` and `pydantic`

# Installation

```bash
pip install rss-parser
```

or

```bash
git clone https://github.com/dhvcc/rss-parser.git
cd rss-parser
pip install .
```

# Usage

```python
from rss_parser import Parser
from requests import get

rss_url = "https://feedforall.com/sample.xml"
xml = get(rss_url)

# Limit feed output to 5 items
# To disable limit simply do not provide the argument or use None
parser = Parser(xml=xml.content, limit=5)
feed = parser.parse()

# Print out feed meta data
print(feed.language)
print(feed.version)

# Iteratively print feed items
for item in feed.feed:
    print(item.title)
    print(item.description)

```

# Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

# License

[GPLv3](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)
