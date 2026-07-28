# Parsing feeds

## Supported feed types

| Feed type | Root element | Parser | Model |
| --- | --- | --- | --- |
| RSS 2.0 / 0.9x | `<rss>` | `RSSParser` | `rss_parser.models.rss.RSS` |
| Atom 1.0 | `<feed>` | `AtomParser` | `rss_parser.models.atom.Atom` |
| RSS 1.0 (RDF) | `<rdf:RDF>` | `RDFParser` | `rss_parser.models.rdf.RDF` |
| Podcast (RSS 2.0 + iTunes) | `<rss>` | `PodcastParser` | `rss_parser.models.rss.itunes.Podcast` |

RSS 0.91/0.92 feeds are a structural subset of RSS 2.0 and parse with the same model —
check `rss.version` to see what the document declared.

## Automatic detection

`parse()` inspects the root element and picks the right parser:

```python
from rss_parser import parse
from rss_parser.models.rss import RSS
from rss_parser.models.atom import Atom

feed = parse(data)

if isinstance(feed, RSS):
    print("RSS", feed.version)
elif isinstance(feed, Atom):
    print("Atom", feed.feed.title)
```

You can also detect without parsing the whole schema:

```python
from rss_parser import detect_feed_type, FeedType

detect_feed_type(data)  # FeedType.RSS | FeedType.ATOM | FeedType.RDF
```

If the document's root is not a known feed root, both raise `UnknownFeedTypeError`:

```python
from rss_parser import UnknownFeedTypeError

try:
    feed = parse(data)
except UnknownFeedTypeError as e:
    print(e)
# Could not detect the feed type from root element(s) ['html']. Supported roots are
# <rss> (RSS 0.9x/2.0), <feed> (Atom 1.0) and <rdf:RDF> (RSS 1.0). ...
```

### Overriding the parser per feed type

`parse()` accepts a `parsers` mapping, so you can e.g. get typed podcast fields
while keeping automatic detection:

```python
from rss_parser import parse, FeedType, PodcastParser

feed = parse(data, parsers={FeedType.RSS: PodcastParser})
```

## Explicit parsers

When you know the feed type, skip detection:

```python
from rss_parser import RSSParser, AtomParser, RDFParser, PodcastParser

rss = RSSParser.parse(data)
```

Every parser accepts a `schema` override (see [Customizing the schema](extending.md))
and a `root_key` override for unusual documents:

```python
rss = RSSParser.parse(data, schema=MySchema, root_key="rss")
```

## RSS 1.0 (RDF) specifics

RSS 1.0 predates RSS 2.0 and has a different shape: the items are *siblings* of the channel,
not children of it.

```python
from rss_parser import RDFParser

rdf = RDFParser.parse(data)

rdf.channel.title      # channel metadata
rdf.items              # the actual items, at the document root
rdf.items[0].attributes["rdf:about"]  # the item's RDF identifier
```

Dublin Core (`dc:*`) and syndication (`syn:*`) module tags are not dropped —
they are available via `model_extra`:

```python
rdf.channel.content.model_extra["dc:publisher"]
```

## Error handling

The full error contract:

| Problem | Raised |
| --- | --- |
| Data is not well-formed XML | `InvalidXMLError` (the original `ExpatError` is `__cause__`) |
| Well-formed XML, but not a known feed root | `UnknownFeedTypeError` (only from `parse()`/`detect_feed_type()`) |
| Valid feed XML that violates the schema | pydantic `ValidationError` |
| Document declares a DTD entity | `ValueError("entities are disabled")` from xmltodict |

Entity declarations are refused before expansion, so external-entity (XXE) and
entity-expansion feeds never get processed — see
[SECURITY.md](https://github.com/dhvcc/rss-parser/blob/master/SECURITY.md).

Both rss-parser errors subclass `ValueError`, so `except ValueError` catches everything
except schema violations.

```python
from rss_parser import parse, InvalidXMLError, UnknownFeedTypeError
from pydantic import ValidationError

try:
    feed = parse(data)
except InvalidXMLError:
    ...  # not XML
except UnknownFeedTypeError:
    ...  # XML, but not a feed
except ValidationError:
    ...  # a feed, but breaks the schema rules
```

Validation errors are raised as pydantic `ValidationError` with a precise path to the problem:

```
1 validation error for RSS
channel.content.item.0.content
  Value error, either <title> or <description> must be present in an <item> [type=value_error, ...]
```

Required fields follow the specs with one deliberate exception: an RSS channel must have
`title`, `link` and `description`; an item must have at least one of `title`/`description`;
an Atom feed/entry must have `id` and `title`. Atom's `updated` is required by the spec but
optional here, because major real-world publishers omit it (YouTube's feeds have no
feed-level `<updated>`).
