# Rss parser

[![Downloads](https://pepy.tech/badge/rss-parser)](https://pepy.tech/project/rss-parser)
[![Downloads](https://pepy.tech/badge/rss-parser/month)](https://pepy.tech/project/rss-parser/month)
[![Downloads](https://pepy.tech/badge/rss-parser/week)](https://pepy.tech/project/rss-parser/week)

[![PyPI version](https://img.shields.io/pypi/v/rss-parser)](https://pypi.org/project/rss-parser)
[![Python versions](https://img.shields.io/pypi/pyversions/rss-parser)](https://pypi.org/project/rss-parser)
[![Wheel status](https://img.shields.io/pypi/wheel/rss-parser)](https://pypi.org/project/rss-parser)
[![License](https://img.shields.io/pypi/l/rss-parser?color=success)](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)
[![GitHub Pages](https://badgen.net/github/status/dhvcc/rss-parser/gh-pages?label=docs)](https://dhvcc.github.io/rss-parser#documentation)

![CI](https://github.com/dhvcc/rss-parser/actions/workflows/ci.yml/badge.svg?branch=master)
![PyPi publish](https://github.com/dhvcc/rss-parser/actions/workflows/publish_to_pypi.yml/badge.svg?branch=master)

## About

`rss-parser` is typed python RSS parsing module built using [pydantic](https://github.com/pydantic/pydantic) and [xmltodict](https://github.com/martinblech/xmltodict)

## Installation

```bash
pip install rss-parser
```

or

```bash
git clone https://github.com/dhvcc/rss-parser.git
cd rss-parser
poetry build
pip install dist/*.whl
```

## Usage

### Quickstart

```python
from rss_parser import Parser
from requests import get

rss_url = "https://feedforall.com/sample.xml"
xml = get(rss_url)

# Limit feed output to 5 items
parser = Parser(xml=xml.content, limit=5)
rss = parser.parse()

# Print out rss meta data
print(rss.channel.language)
print(rss.version)

# Iteratively print feed items
for item in rss.channel.feed:
    print(item.title)
    print(item.description)

```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Install dependencies with `poetry install` (`pip install poetry`)

`pre-commit` usage is highly recommended. To install hooks run

```bash
poetry run pre-commit install -t=pre-commit -t=pre-push
```

## License

[GPLv3](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)
