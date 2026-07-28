# Quickstart

## Parse a feed

```python
from rss_parser import parse
from requests import get  # noqa

rss_url = "https://rss.art19.com/apology-line"
response = get(rss_url)

feed = parse(response.content)

# Print out feed meta data
print("Language", feed.channel.language)
print("RSS", feed.version)

# Iteratively print feed items
for item in feed.channel.items:
    print(item.title)
    print(str(item.description)[:50])
```

```
Language en
RSS 2.0
Wondery Presents - Flipping The Bird: Elon vs Twitter
<p>When Elon Musk posted a video of himself arrivi
Introducing: The Apology Line
<p>If you could call a number and say you’re sorry
```

`parse()` detects the feed type from the XML root element and returns the matching typed model —
[`RSS`][parsing], [`Atom`][parsing] or [`RDF`][parsing]. If you already know what you're parsing,
use the explicit parser classes instead:

```python
from rss_parser import RSSParser, AtomParser, RDFParser, PodcastParser

rss = RSSParser.parse(rss_xml)
atom = AtomParser.parse(atom_xml)
```

[parsing]: parsing.md

!!! note "Description still contains HTML?"
    In the output above the description contains `<p>` tags — that's because the feed wraps it in
    [CDATA](https://www.w3resource.com/xml/CDATA-sections.php):

    ```
    <![CDATA[<p>If you could call ...</p>]]>
    ```

    `rss-parser` gives you the feed's data as-is; sanitizing embedded HTML is up to you.

## Tags: content and attributes

Every XML tag is wrapped in a `Tag` object that separates the text from the XML attributes:

```python
item = feed.channel.items[0]

item.title.content        # "Wondery Presents - ..." - the typed value
item.title.attributes     # {} - dict of XML attributes, @-prefix stripped, snake_cased

str(item.title)           # same as str(item.title.content)
item.title.upper()        # attribute access is forwarded to the content
```

Self-closing tags like `<enclosure url="..." length="..." type="..."/>` have `content=None` and
their data in `.attributes`:

```python
enclosure = item.enclosures[0]
enclosure.attributes["url"]   # "https://..."
```

## Serialize back to JSON

```python
feed.model_dump()        # full structure, Tag objects as {"content": ..., "attributes": ...}
feed.json_plain()        # flattened: every Tag becomes just its content value
```

## Next steps

- [Parsing feeds](parsing.md) — feed types and detection in depth.
- [Customizing the schema](extending.md) — add your own fields.
- [Podcasts](podcasts.md) — typed `itunes:*` support.
