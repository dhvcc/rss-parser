# Customizing the schema

RSS in the wild is full of namespaced extensions (`itunes:*`, `media:*`, `dc:*`, custom vendor tags).
`rss-parser` keeps the default schemas strict and spec-shaped, but makes it cheap to bolt on your own fields.

## Unknown tags are kept

Before writing any code, check if you need to: every tag that is not declared on the schema
is preserved in `model_extra`, not thrown away.

```python
from rss_parser import RSSParser

rss = RSSParser.parse(podcast_xml)

rss.channel.content.model_extra["itunes:author"]
# 'Wondery'
```

That's untyped, though. For typed access, declare fields.

## Add typed fields: one subclass, one parametrization

The core models are **generic**: `Channel` is generic over its item type, `RSS` over its channel type
(`Feed`/`Atom` likewise for Atom entries/feeds). To extend the item schema you subclass `Item`
and parametrize — no need to re-declare the channel or root models:

```python
from typing import Optional
from pydantic import Field

from rss_parser import RSSParser
from rss_parser.models.rss import RSS, Channel, Item
from rss_parser.models.types import Tag


class MyItem(Item):
    media_content: Optional[Tag[dict]] = Field(alias="media:content", default=None)
    dc_creator: Optional[Tag[str]] = Field(alias="dc:creator", default=None)


rss = RSSParser.parse(data, schema=RSS[Channel[MyItem]])

rss.channel.items[0].content.dc_creator
```

Channel-level tags work the same way:

```python
class MyChannel(Channel[MyItem]):
    webfeeds_icon: Optional[Tag[str]] = Field(alias="webfeeds:icon", default=None)


rss = RSSParser.parse(data, schema=RSS[MyChannel])
```

!!! tip "Namespaced tags need an explicit alias"
    Field aliases are generated in camelCase (`pub_date` -> `pubDate`), but XML namespace prefixes
    contain a colon, so declare them explicitly: `Field(alias="media:content")`.

!!! tip "Podcasts are pre-built"
    For `itunes:*` tags you don't need any of this — see [Podcasts](podcasts.md).

## Reusable mixins

If you use the same extension tags across projects, package them as a mixin
(this is exactly how the built-in iTunes support is implemented):

```python
from rss_parser.models import XMLBaseModel


class MediaRSSMixin(XMLBaseModel):
    """https://www.rssboard.org/media-rss"""

    media_content: Optional[Tag[dict]] = Field(alias="media:content", default=None)
    media_thumbnail: Optional[Tag[dict]] = Field(alias="media:thumbnail", default=None)


class MediaItem(MediaRSSMixin, Item):
    pass


rss = RSSParser.parse(data, schema=RSS[Channel[MediaItem]])
```

## Field types cheat sheet

| XML shape | Field declaration |
| --- | --- |
| `<tag>text</tag>` | `Optional[Tag[str]] = None` |
| `<tag>42</tag>` | `Optional[Tag[int]] = None` |
| `<tag attr="x"/>` (attribute-only) | `Optional[Tag[str]] = None`, read `.attributes` |
| Repeatable tag | `OnlyList[Tag[str]] = Field(alias="tag", default_factory=OnlyList)` |
| Tag with children | `Optional[Tag[MyChildModel]] = None` |
| Anything, kept raw | `Optional[Tag[dict]] = None` |

`OnlyList` (from `rss_parser.models.types`) normalizes the xmltodict quirk where a single
occurrence is a dict but multiple occurrences are a list — with it, the field is *always* a list.

## Replacing the schema entirely

The `schema` argument accepts any `XMLBaseModel`, so you can parse arbitrary XML documents
with the same machinery:

```python
from rss_parser import RSSParser
from rss_parser.models import XMLBaseModel
from rss_parser.models.types import Tag


class CustomSchema(XMLBaseModel):
    custom: Tag[str]


rss = RSSParser.parse('<rss version="2.0"><custom>Custom tag data</custom></rss>', schema=CustomSchema)

print(rss.custom)
# Custom tag data
```
