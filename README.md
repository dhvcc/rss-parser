# Rss parser

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

Here we can see that description is still somehow has <p> - this is beacause it's placed as [CDATA](https://www.w3resource.com/xml/CDATA-sections.php) like so

```xml
<![CDATA[<p>If you could call ...</p>]]>
```

### Overriding schema

If you want to customize the schema or provide a custom one - use `schema` keyword argument of the parser

```python
from rss_parser.models import XMLBaseModel
from rss_parser.models.rss import RSS
from rss_parser.models.types import Tag

class CustomSchema(RSS, XMLBaseModel):
    channel: None = None # Removing previous channel field
    custom: Tag[str]

with open("tests/samples/custom.xml") as f:
    data = f.read()

rss = Parser.parse(data, schema=CustomSchema)

print("RSS", rss.version)
print("Custom", rss.custom)

# RSS 2.0
# Custom Custom tag data
```

### xmltodict

This library uses [xmltodict](https://github.com/martinblech/xmltodict) to parse XML data. You can see the detailed documentation [here](https://github.com/martinblech/xmltodict#xmltodict)

The basic thing you should know is that your data is processed into dictionaries

For example, this data

```xml
<tag>content</tag>
```

will result in the following

```python
{
    "tag": "content"
}
```

*But*, when handling attributes, the content of the tag will be also a dictionary

```xml
<tag attr="1" data-value="data">data</tag>
```

Turns into

```python
{
    "tag": {
        "@attr": "1",
        "@data-value": "data",
        "#text": "content"
    }
}
```

### Tag field

This is a generic field that handles tags as raw data or a dictonary returned with attributes

*Although this is a complex class, it forwards most of the methods to it's content attribute, so you don't notice a difference if you're only after the .content value*

Example

```python
from rss_parser.models import XMLBaseModel
class Model(XMLBaseModel):
     number: Tag[int]
     string: Tag[str]

m = Model(
    number=1,
    string={'@attr': '1', '#text': 'content'},
)

m.number.content == 1  # Content value is an integer, as per the generic type

m.number.content + 10 == m.number + 10  # But you're still able to use the Tag itself in common operators

m.number.bit_length() == 1  # As it's the case for methods/attributes not found in the Tag itself

type(m.number), type(m.number.content) == (<class 'rss_parser.models.image.Tag[int]'>, <class 'int'>)  # types are NOT the same, however, the interfaces are very similar most of the time

m.number.attributes == {}  # The attributes are empty by default

m.string.attributes == {'attr': '1'}  # But are populated when provided. Note that the @ symbol is trimmed from the beggining, however, camelCase is not converted

# Generic argument types are handled by pydantic - let's try to provide a string for a Tag[int] number

m = Model(number='not_a_number', string={'@customAttr': 'v', '#text': 'str tag value'})  # This will lead in the following traceback

# Traceback (most recent call last):
#     ...
# pydantic.error_wrappers.ValidationError: 1 validation error for Model
# number -> content
#     value is not a valid integer (type=type_error.integer)
```

**If you wish to avoid all of the method/attribute forwarding "magic" - you should use `rss_parser.models.types.TagRaw`**

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
