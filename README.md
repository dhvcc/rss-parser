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

rss_url = "https://rss.art19.com/apology-line"
response = get(rss_url)

rss = Parser.parse(response.text)

# Print out rss meta data
print("Language", rss.channel.language)
print("RSS", rss.version)

# Iteratively print feed items
for item in rss.channel.items:
    print(item.title)
    print(item.description[:50])

# Language en
# RSS 2.0
# Wondery Presents - Flipping The Bird: Elon vs Twitter
# <p>When Elon Musk posted a video of himself arrivi
# Introducing: The Apology Line
# <p>If you could call a number and say you’re sorry
```

Here we can see that description is still somehow has <p> - this is beacause it's places as CDATA

#### Overriding schema

If you want to customize the schema or provide a custom one - use `schema` keyword argument of the parser

```python
from rss_parser.models import XMLBaseModel
from rss_parser.models.rss import RSS
from rss_parser.models.types import Tag

class CustomSchema(RSS, XMLBaseModel):
    # Removing previous channel field
    channel: None = None
    custom: Tag[str]

with open("tests/samples/custom.xml") as f:
    data = f.read()

rss = Parser.parse(data, schema=CustomSchema)

print("RSS", rss.version)
print("Custom", rss.custom)

# RSS 2.0
# Custom Custom tag data
```

#### Tag field

Class to represent XML tag.

For example, this tag <tag>123</tag> will result in 'tag': '123' in parent dict.
However, if we add any attributes to it <tag someAttr="val">123</tag>,
then the value will not be '123', but {'@someAttr':'val','#text': '123'}.
This class allows you to handle this dynamically.

```python
>>> from rss_parser.models import XMLBaseModel
>>> class Model(XMLBaseModel):
...     number: Tag[int]
...     string: Tag[str]
>>> m = Model(number=1, string={'@customAttr': 'v', '#text': 'str tag value'})
>>> m.number.content
1
>>> m.number + 10  # forwarding operators to m.number.content for simplicity
11
>>> m.number.bit_length()  # forwarding getattr to m.number.content
1
>>> type(m.number), type(m.number.content)
(rss_parser.models.image.Tag[int], int)  # types are NOT the same, however, the interfaces are similar
>>> m.number.attributes
{}
>>> m.string.content
'str tag value'
>>> m.string.attributes
{'customAttr': 'v'}
>>> m = Model(number='not_a_number', string={'@customAttr': 'v', '#text': 'str tag value'})
Traceback (most recent call last):
    ...
pydantic.error_wrappers.ValidationError: 1 validation error for Model
number -> content
    value is not a valid integer (type=type_error.integer)
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
