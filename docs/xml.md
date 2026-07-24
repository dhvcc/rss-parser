# How XML is handled

`rss-parser` uses [xmltodict](https://github.com/martinblech/xmltodict) to convert XML into
dictionaries, then validates those with pydantic. Knowing the intermediate shape helps when
declaring custom fields.

## The xmltodict shape

A simple tag becomes a plain value:

```xml
<tag>content</tag>
```

```python
{"tag": "content"}
```

A tag with attributes becomes a dict — attributes are prefixed with `@`, the text lives under `#text`:

```xml
<tag attr="1" data-value="data">content</tag>
```

```python
{
    "tag": {
        "@attr": "1",
        "@data-value": "data",
        "#text": "content",
    }
}
```

A repeated tag becomes a list:

```xml
<div>
    <tag>content</tag>
    <tag>content2</tag>
</div>
```

```python
{"div": {"tag": ["content", "content2"]}}
```

## The Tag field

`Tag[T]` absorbs the first two shapes so you never touch `@`/`#text` keys:

```python
from rss_parser.models import XMLBaseModel
from rss_parser.models.types import Tag


class Model(XMLBaseModel):
    width: Tag[int]
    category: Tag[str]


m = Model.model_validate(
    {
        "width": 48,
        "category": {"@someAttribute": "https://example.com", "#text": "valid string"},
    }
)

m.width.content        # 48 - typed per the generic argument
m.width.attributes     # {}
m.category.attributes  # {'some_attribute': 'https://example.com'}
str(m.category)        # 'valid string'
m.category.upper()     # 'VALID STRING' - attribute access is forwarded to content
```

Attribute keys have the `@` stripped and are converted to snake_case.

For self-closing tags (`<cloud domain="..."/>`), `content` is `None` and everything is
in `.attributes`. Accessing a forwarded attribute on an empty tag raises a clear `AttributeError`
telling you to look at `.attributes`.

## The OnlyList field

`OnlyList[T]` absorbs the third shape — a field declared with it is always a list, whether the
tag appeared once, many times, or not at all:

```python
from pydantic import Field
from rss_parser.models.types import OnlyList, Tag


class MyChannel(XMLBaseModel):
    items: OnlyList[Tag[Item]] = Field(alias="item", default_factory=OnlyList)
```

## Dates

Fields typed `Tag[DateTimeOrStr]` (like `pub_date`) try RFC 822 first (the RSS standard),
then ISO 8601/timestamps. If nothing matches, the raw string is kept instead of erroring —
dates in the wild are too messy to reject a whole feed over one of them.

## Aliases

Field names are snake_case in Python and camelCase in XML; the alias generator handles the
conversion (`pub_date` -> `pubDate`, `managing_editor` -> `managingEditor`).
Namespaced tags (with `:`) always need an explicit alias: `Field(alias="itunes:duration")`.
