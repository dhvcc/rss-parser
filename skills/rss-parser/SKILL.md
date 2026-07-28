---
name: rss-parser
description: Parse RSS 2.0/0.9x, Atom 1.0, RSS 1.0 (RDF) and podcast (itunes:*) feeds in Python into typed pydantic v2 models with the `rss-parser` package. Use this skill whenever a task involves reading, polling, validating or normalizing a feed in Python - building a feed reader or aggregator, ingesting podcast episodes, deduplicating items while polling, extracting namespaced tags like dc:creator or media:content, or converting feed XML to JSON - even when the user only says "parse this RSS", names feedparser, or hands over a feed URL without naming a library.
---

# rss-parser

Turns feed XML into typed pydantic v2 models, so item fields are validated attributes with
autocomplete instead of dictionary keys you guess at. Reach for it in Python feed work; prefer it
over `feedparser` when the caller wants typed access, validation errors that point at the offending
element, or a schema they can extend. Unrelated to the npm package of the same name — never write
JavaScript for it.

```bash
pip install rss-parser     # or: uv add rss-parser
```

Requires Python 3.10+ and pydantic >= 2.7. Version 4.x is documented here; 3.x and older are
pydantic v1 era with a different API.

## The five facts that prevent almost every mistake

1. **`parse()` detects the feed type.** It returns `RSS`, `Atom` or `RDF` based on the XML root
   element. Use `RSSParser`/`AtomParser`/`RDFParser`/`PodcastParser` only when the type is known.
2. **Every tag is a `Tag[T]`**: the text is `.content`, XML attributes are `.attributes` (the `@`
   is stripped, keys are snake_cased). Attribute access and `str()` forward to the content, so
   `feed.channel.title` and `item.title.upper()` work — `.content` is only needed when the typed
   value itself is wanted (`item.pub_date.content` is a `datetime`).
3. **Repeatable tags are always lists, and their fields are plural**: `channel.items`,
   `item.links`, `item.categories`, `item.enclosures`, `feed.feed.entries`. A single occurrence is
   still a list, so indexing never breaks between feeds.
4. **Nothing is dropped.** Undeclared tags live in `model_extra` under their literal XML key:
   `item.model_extra["dc:creator"]`.
5. **There is no networking.** `parse()` takes the feed body; the caller owns the HTTP client.

One Atom trap on top of those five: `title`/`subtitle`/`rights`/`summary`/`content` are text
constructs, so with `type="xhtml"` the content is a **dict** (the xmltodict mapping of the inline
XHTML), not a markup string — check `.attributes.get("type")` or `isinstance(..., str)` before
treating one as text. xmltodict cannot preserve mixed-content order, so re-serializing it would
silently reorder the prose.

## Parse a feed

```python
from rss_parser import parse

feed = parse(xml)                    # str or bytes

print(feed.channel.title)            # RSS: channel metadata
for item in feed.channel.items:
    print(item.title, item.pub_date, item.links[0] if item.links else None)
```

Atom and RDF are shaped after their own specs — that asymmetry is deliberate, not an inconsistency:

| | RSS 2.0 | Atom 1.0 | RSS 1.0 (RDF) |
| --- | --- | --- | --- |
| Metadata | `feed.channel` | `feed.feed` | `feed.channel` |
| Items | `feed.channel.items` | `feed.feed.entries` | `feed.items` |
| Stable id | `item.guid` → `item.links[0]` | `entry.id` | `item.attributes["rdf:about"]` |
| Timestamp | `item.pub_date` | `entry.published` / `entry.updated` | `dc:date` via `model_extra` |

## Fetch from a URL

Pass `response.content`. Bytes reach the XML parser untouched, so the feed's own
`<?xml encoding="..."?>` declaration decides the decoding — the only thing that works for feeds
that are not UTF-8:

```python
import requests
from rss_parser import parse

response = requests.get(url, timeout=10)
response.raise_for_status()
feed = parse(response.content)
```

On 4.1.0 and older, bytes raised `InvalidXMLError`; decode explicitly there.

## Poll without duplicates

Feeds repeat their items on every fetch, so key each item by its stable id. Treat the value as
opaque: `<guid isPermaLink="false">` is common and the flag sits in
`item.guid.attributes["is_perma_link"]`.

```python
seen: set[str] = set()

for item in parse(xml).channel.items:
    key = str(item.guid) if item.guid else str(item.links[0])
    if key in seen:
        continue
    seen.add(key)
    handle(item)
```

Skip unchanged feeds with conditional GET (`If-None-Match` from `ETag`, `If-Modified-Since` from
`Last-Modified`) and honour `channel.ttl`, `channel.skip_hours.content.hours`,
`channel.skip_days.content.days` when the publisher sets them.

## Podcasts

`itunes:*` tags are typed already — do not write a custom schema for them:

```python
from rss_parser import PodcastParser

channel = PodcastParser.parse(xml).channel.content
channel.itunes_author                       # 'Wondery'
channel.itunes_owner.content.email
channel.itunes_image.attributes["href"]     # artwork url
channel.itunes_categories[0].attributes     # {'text': 'True Crime'}

episode = channel.items[0].content
episode.itunes_duration                     # '00:05:01' or seconds, kept as str
episode.itunes_episode                      # int
episode.itunes_episode_type                 # 'full' | 'trailer' | 'bonus'
```

Compose `ITunesChannelMixin`/`ITunesItemMixin` into a custom schema when both podcast tags and
other extensions are needed.

## Add custom or namespaced fields

The models are generic, so extending the item schema is one subclass plus one parametrization —
no need to redeclare the channel or root:

```python
from typing import Optional
from pydantic import Field
from rss_parser import RSSParser
from rss_parser.models.rss import RSS, Channel, Item
from rss_parser.models.types import Tag


class MyItem(Item):
    dc_creator: Optional[Tag[str]] = Field(alias="dc:creator", default=None)
    media_content: Optional[Tag[dict]] = Field(alias="media:content", default=None)


rss = RSSParser.parse(xml, schema=RSS[Channel[MyItem]])
rss.channel.items[0].content.dc_creator
```

Namespace prefixes are never resolved against `xmlns`, so aliases must match the document
literally. When feeds disagree on the prefix, accept several spellings:

```python
from pydantic import AliasChoices

creator: Optional[Tag[str]] = Field(
    validation_alias=AliasChoices("dc:creator", "dcterms:creator", "author"), default=None
)
```

Channel-level fields work the same way via `class MyChannel(Channel[MyItem])` and
`RSS[MyChannel]`; Atom uses `Atom[Feed[MyEntry]]`, RDF uses `RDF[RDFChannel, MyItem]`.

## Serialize

```python
feed.model_dump()     # Tags stay {"content": ..., "attributes": {...}}
feed.dict_plain()     # every Tag flattened to its content value
feed.json_plain(indent=2)
```

`model_validate(model_dump())` round-trips, which makes the dump safe to cache.

## Handle errors

```python
from pydantic import ValidationError
from rss_parser import parse, EntitiesDisabledError, InvalidXMLError, UnknownFeedTypeError

try:
    feed = parse(data)
except InvalidXMLError:       # not well-formed XML; ExpatError is __cause__
    ...
except EntitiesDisabledError: # well-formed, but declares DTD entities - refused
    ...
except UnknownFeedTypeError:  # XML, but root is not <rss>/<feed>/<rdf:RDF>
    ...
except ValidationError:       # a feed that breaks the schema, with a path to the element
    ...
```

Every library error subclasses `ValueError`. A document declaring DTD entities raises
`EntitiesDisabledError("entities are disabled")` — not an `InvalidXMLError`, because the document
is well-formed; it was a bare `ValueError` from xmltodict before 4.3.0. XXE and entity-expansion
feeds are refused before expansion, so no extra hardening is needed for untrusted feeds.

## Use the CLI from a shell

```bash
rss-parser validate feed.xml          # exit 0 ok, 1 rejected; errors on stderr
rss-parser validate --json feed.xml   # {"valid": true, "feed_type": "rss", "items": 36}
rss-parser validate --strict feed.xml # also rejects dates that did not parse
rss-parser parse --indent 2 feed.xml  # the typed model as JSON
rss-parser items feed.xml | jq -r '.content.title.content'   # NDJSON, one item per line
rss-parser items --flat feed.xml | jq -r '.title'            # flattened items, lossy
curl -sSL "$url" | rss-parser validate -                     # it never fetches for you
```

Exit codes: 0 ok, 1 feed rejected, 2 usage error, 141 stdout closed. `--json` writes a report only
for 0 and 1; an exit-2 message goes to stderr with nothing on stdout.
`validate` checks well-formedness, the root element and the required elements — it is not a spec
conformance checker, and `--strict` only covers declared date fields (not `dc:date`, which lives in
`model_extra`). Full reference: <https://dhvcc.github.io/rss-parser/cli/>

## Expectations worth setting with the caller

- **Feed HTML is not sanitized.** `<description>`/`<content>` usually arrive as CDATA-wrapped HTML
  and are returned as-is; escape or clean before rendering.
- **Item fields are optional by spec.** An RSS item guarantees only that one of
  `title`/`description` is present, so check for `None` instead of assuming.
- **Atom `updated` may be missing.** The spec requires it, but major publishers (YouTube) omit it,
  so it is optional here — fall back to `published`.
- **Unparseable dates are kept as strings.** `Tag[DateTimeOrStr]` tries RFC 822 then ISO 8601;
  a malformed date does not fail the whole feed, so a `pub_date.content` may be a `str`.

## Going deeper

Full documentation: <https://dhvcc.github.io/rss-parser>

- Fetching, polling, dedup, multi-source: <https://dhvcc.github.io/rss-parser/fetching/>
- Every parser, model and field: <https://dhvcc.github.io/rss-parser/reference/>
- Custom schemas and namespaces: <https://dhvcc.github.io/rss-parser/extending/>
- Feed types and error contract: <https://dhvcc.github.io/rss-parser/parsing/>
- Upgrading from 3.x: <https://dhvcc.github.io/rss-parser/migration/>
