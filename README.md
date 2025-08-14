# RSS Parser

[![Downloads](https://pepy.tech/badge/rss-parser)](https://pepy.tech/project/rss-parser)
[![Downloads](https://pepy.tech/badge/rss-parser/month)](https://pepy.tech/project/rss-parser)
[![Downloads](https://pepy.tech/badge/rss-parser/week)](https://pepy.tech/project/rss-parser)

[![PyPI version](https://img.shields.io/pypi/v/rss-parser)](https://pypi.org/project/rss-parser)
[![Python versions](https://img.shields.io/pypi/pyversions/rss-parser)](https://pypi.org/project/rss-parser)
[![Wheel status](https://img.shields.io/pypi/wheel/rss-parser)](https://pypi.org/project/rss-parser)
[![License](https://img.shields.io/pypi/l/rss-parser?color=success)](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)

![Docs](https://github.com/dhvcc/rss-parser/actions/workflows/pages/pages-build-deployment/badge.svg)
![CI](https://github.com/dhvcc/rss-parser/actions/workflows/ci.yml/badge.svg?branch=master)
![PyPi publish](https://github.com/dhvcc/rss-parser/actions/workflows/publish_to_pypi.yml/badge.svg)

## About

`rss-parser` is a type-safe Python RSS/Atom parsing module built using [pydantic](https://github.com/pydantic/pydantic) and [xmltodict](https://github.com/martinblech/xmltodict).

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

## V1 -> V2 Migration
- The `Parser` class has been renamed to `RSSParser`
- Models for RSS-specific schemas have been moved from `rss_parser.models` to `rss_parser.models.rss`. Generic types remain unchanged
- Date parsing has been improved and now uses pydantic's `validator` instead of `email.utils`, producing better datetime objects where it previously defaulted to `str`

## Usage

### Quickstart

**NOTE: For parsing Atom, use `AtomParser`**

```python
from rss_parser import RSSParser
from requests import get  # noqa

rss_url = "https://rss.art19.com/apology-line"
response = get(rss_url)

rss = RSSParser.parse(response.text)

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

Here we can see that the description still contains `<p>` tags - this is because it's wrapped in [CDATA](https://www.w3resource.com/xml/CDATA-sections.php) like so:

```
<![CDATA[<p>If you could call ...</p>]]>
```

### Overriding Schema

If you want to customize the schema or provide a custom one, use the `schema` keyword argument of the parser:

```python
from rss_parser import RSSParser
from rss_parser.models import XMLBaseModel
from rss_parser.models.rss import RSS
from rss_parser.models.types import Tag


class CustomSchema(RSS, XMLBaseModel):
    channel: None = None  # Removing previous channel field
    custom: Tag[str]


with open("tests/samples/custom.xml") as f:
    data = f.read()

rss = RSSParser.parse(data, schema=CustomSchema)

print("RSS", rss.version)
print("Custom", rss.custom)

# RSS 2.0
# Custom Custom tag data
```

### xmltodict

This library uses [xmltodict](https://github.com/martinblech/xmltodict) to parse XML data. You can find the detailed documentation [here](https://github.com/martinblech/xmltodict#xmltodict).

The key thing to understand is that your data is processed into dictionaries.

For example, this XML:

```xml
<tag>content</tag>
```

will result in the following dictionary:

```python
{
    "tag": "content"
}
```

*However*, when handling attributes, the content of the tag will also be a dictionary:

```xml
<tag attr="1" data-value="data">data</tag>
```

This becomes:

```python
{
    "tag": {
        "@attr": "1",
        "@data-value": "data",
        "#text": "content"
    }
}
```

Multiple children of a tag will be placed into a list:

```xml
<div>
    <tag>content</tag>
    <tag>content2</tag>
</div>
```

This results in a list:

```python
[
    { "tag": "content" },
    { "tag": "content" },
]
```

If you don't want to deal with these conditions and want to parse something **always** as a list, please use `rss_parser.models.types.only_list.OnlyList` like we did in `Channel`:
```python
from typing import Optional

from rss_parser.models.rss.item import Item
from rss_parser.models.types.only_list import OnlyList
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()
...


class OptionalChannelElementsMixin(...):
    ...
    items: Optional[OnlyList[Tag[Item]]] = pydantic.Field(alias="item", default=[])
```

### Tag Field

This is a generic field that handles tags as raw data or as a dictionary returned with attributes.

Example:

```python
from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class Model(XMLBaseModel):
    width: Tag[int]
    category: Tag[str]


m = Model(
    width=48,
    category={"@someAttribute": "https://example.com", "#text": "valid string"},
)

# Content value is an integer, as per the generic type
assert m.width.content == 48

assert type(m.width), type(m.width.content) == (Tag[int], int)

# The attributes are empty by default
assert m.width.attributes == {} # But are populated when provided.

# Note that the @ symbol is trimmed from the beginning and the name is converted to snake_case
assert m.category.attributes == {'some_attribute': 'https://example.com'}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Install dependencies with `poetry install` (`pip install poetry`).

Using `pre-commit` is highly recommended. To install hooks, run:

```bash
poetry run pre-commit install -t=pre-commit -t=pre-push
```

## License

[GPLv3](https://github.com/dhvcc/rss-parser/blob/master/LICENSE)
