# API reference

Every public name lives on the package root: `from rss_parser import parse, RSSParser, ...`.

## Core API

| Callable | Signature | Returns |
| --- | --- | --- |
| `parse` | `parse(data, *, parsers=None)` | `RSS`, `Atom` or `RDF`, chosen by the XML root element |
| `detect_feed_type` | `detect_feed_type(data)` | `FeedType.RSS` / `FeedType.ATOM` / `FeedType.RDF` |
| `RSSParser.parse` | `parse(data, *, schema=None, root_key=None)` | `RSS` |
| `AtomParser.parse` | same | `Atom` |
| `RDFParser.parse` | same | `RDF` |
| `PodcastParser.parse` | same | `Podcast` (RSS 2.0 + `itunes:*`) |
| `BaseParser.parse_dict` | `parse_dict(root, *, schema=None, root_key=None)` | parses an already `xmltodict`-converted mapping |

```python
from rss_parser import parse, detect_feed_type, FeedType, PodcastParser

feed = parse(xml)                                        # detection
feed = parse(xml, parsers={FeedType.RSS: PodcastParser})  # detection + typed itunes:*
kind = detect_feed_type(xml)                             # detection only
```

`parse()` needs no HTTP client. It accepts `str` or `bytes`; bytes are handed to the XML parser
untouched, so the document's `<?xml encoding="..."?>` declaration is honored — prefer them for
feeds that are not UTF-8. See [Fetching feeds from a URL](fetching.md).

### Errors

| Raised | When |
| --- | --- |
| `InvalidXMLError` | data is not well-formed XML (`ExpatError` is `__cause__`) |
| `UnknownFeedTypeError` | well-formed XML whose root is not `<rss>`, `<feed>` or `<rdf:RDF>` |
| pydantic `ValidationError` | a feed that violates the schema |
| `EntitiesDisabledError` | the document declares DTD entities (message: `entities are disabled`) |

`InvalidXMLError`, `UnknownFeedTypeError` and `EntitiesDisabledError` subclass `ValueError`.
`EntitiesDisabledError` is deliberately *not* an `InvalidXMLError`: such a document is well-formed,
it is just refused. Details and examples in
[Error handling](parsing.md#error-handling).

## Field types

| Type | Meaning |
| --- | --- |
| `Tag[T]` | one XML tag: `.content` is the typed text (`None` for self-closing tags), `.attributes` is a dict with `@` stripped and keys snake_cased. `str(tag)` gives the content and attribute access is forwarded to it |
| `OnlyList[T]` | a repeatable tag; always a list, whether the tag appeared once, many times or not at all |
| `DateTimeOrStr` | RFC 822 first, then ISO 8601/timestamp; unparseable values are kept as the raw string |
| `TextConstruct` | an Atom text construct (`title`, `subtitle`, `rights`, `summary`, `content`): `str` for `type="text"`/`type="html"`, and the xmltodict `dict` of the child elements for `type="xhtml"`, which is not re-serialized to markup because xmltodict cannot preserve mixed-content order. See [Atom text constructs](parsing.md#atom-text-constructs) |
| `XMLBaseModel` | base of every model: camelCase aliases, `extra="allow"`, plus `dict_plain()`/`json_plain()` |

## Serialization

| Method | Output |
| --- | --- |
| `model_dump()` / `model_dump_json()` | pydantic's dump — each Tag stays `{"content": ..., "attributes": {...}}` |
| `dict_plain(**kwargs)` | same shape with every Tag flattened to its content value |
| `json_plain(*, indent=None, separators=None, sort_keys=False, ensure_ascii=False, **kwargs)` | `dict_plain()` serialized with `json.dumps` |

`model_validate(model_dump())` round-trips. Dump options (`exclude_defaults`, `include`,
`exclude`, `by_alias`) are respected by the plain variants too.

## Feed models

Tags not declared below are never dropped — read them from `model_extra`.
Generic parameters let you swap in your own item/channel types: `RSS[Channel[MyItem]]`,
`Atom[Feed[MyEntry]]`, `RDF[RDFChannel, MyItem]`. See
[Customizing the schema](extending.md).

### RSS 2.0 / 0.9x — `rss_parser.models.rss`

`RSS`

| Field | Type | XML | |
| --- | --- | --- | --- |
| `version` | `Optional[Tag[str]]` | `@version` | optional |
| `channel` | `Tag[ChannelT]` | `channel` | **required** |

`Channel`

| Field | Type | XML | |
| --- | --- | --- | --- |
| `title` | `Tag[str]` | `title` | **required** |
| `link` | `Tag[str]` | `link` | **required** |
| `description` | `Tag[str]` | `description` | **required** |
| `items` | `OnlyList[Tag[ItemT]]` | `item` | optional |
| `language` | `Optional[Tag[str]]` | `language` | optional |
| `copyright` | `Optional[Tag[str]]` | `copyright` | optional |
| `managing_editor` | `Optional[Tag[str]]` | `managingEditor` | optional |
| `web_master` | `Optional[Tag[str]]` | `webMaster` | optional |
| `pub_date` | `Optional[Tag[DateTimeOrStr]]` | `pubDate` | optional |
| `last_build_date` | `Optional[Tag[DateTimeOrStr]]` | `lastBuildDate` | optional |
| `categories` | `OnlyList[Tag[str]]` | `category` | optional |
| `generator` | `Optional[Tag[str]]` | `generator` | optional |
| `docs` | `Optional[Tag[str]]` | `docs` | optional |
| `cloud` | `Optional[Tag[str]]` | `cloud` | optional (attribute-only tag) |
| `ttl` | `Optional[Tag[int]]` | `ttl` | optional |
| `image` | `Optional[Tag[Image]]` | `image` | optional |
| `rating` | `Optional[Tag[str]]` | `rating` | optional |
| `text_input` | `Optional[Tag[TextInput]]` | `textInput` | optional |
| `skip_hours` | `Optional[Tag[SkipHours]]` | `skipHours` | optional |
| `skip_days` | `Optional[Tag[SkipDays]]` | `skipDays` | optional |

`Item` — every field is optional, but at least one of `title`/`description` must be present.

| Field | Type | XML | |
| --- | --- | --- | --- |
| `title` | `Optional[Tag[str]]` | `title` | optional |
| `links` | `OnlyList[Tag[str]]` | `link` | optional |
| `description` | `Optional[Tag[str]]` | `description` | optional |
| `author` | `Optional[Tag[str]]` | `author` | optional |
| `categories` | `OnlyList[Tag[str]]` | `category` | optional |
| `comments` | `Optional[Tag[str]]` | `comments` | optional |
| `enclosures` | `OnlyList[Tag[str]]` | `enclosure` | optional (url/length/type in `.attributes`) |
| `guid` | `Optional[Tag[str]]` | `guid` | optional (`is_perma_link` in `.attributes`) |
| `pub_date` | `Optional[Tag[DateTimeOrStr]]` | `pubDate` | optional |
| `source` | `Optional[Tag[str]]` | `source` | optional (url in `.attributes`) |

`Image`: `url`, `title`, `link` (**required**), `width`, `height`, `description` (optional).
`TextInput`: `title`, `description`, `name`, `link` (all **required**).
`SkipHours`: `hours` — `OnlyList[Tag[int]]` from `<hour>`.
`SkipDays`: `days` — `OnlyList[Tag[str]]` from `<day>`.

### Atom 1.0 — `rss_parser.models.atom`

`Atom`: `version` (`@version`, optional), `feed` (`Tag[FeedT]`, **required**).

`Feed`

| Field | Type | XML | |
| --- | --- | --- | --- |
| `id` | `Tag[str]` | `id` | **required** |
| `title` | `Tag[str]` | `title` | **required** |
| `updated` | `Optional[Tag[DateTimeOrStr]]` | `updated` | optional in practice (see below) |
| `entries` | `OnlyList[Tag[EntryT]]` | `entry` | optional |
| `authors` | `OnlyList[Tag[Person]]` | `author` | optional |
| `links` | `OnlyList[Tag[str]]` | `link` | optional (`rel`/`href` in `.attributes`) |
| `categories` | `OnlyList[Tag[dict]]` | `category` | optional |
| `contributors` | `OnlyList[Tag[Person]]` | `contributor` | optional |
| `generator`, `icon`, `logo`, `rights`, `subtitle` | `Optional[Tag[str]]` | same | optional |

`Entry`

| Field | Type | XML | |
| --- | --- | --- | --- |
| `id` | `Tag[str]` | `id` | **required** |
| `title` | `Tag[str]` | `title` | **required** |
| `updated` | `Optional[Tag[DateTimeOrStr]]` | `updated` | optional in practice |
| `published` | `Optional[Tag[DateTimeOrStr]]` | `published` | optional |
| `links` | `OnlyList[Tag[str]]` | `link` | optional |
| `content` | `Optional[Tag[str]]` | `content` | optional |
| `summary` | `Optional[Tag[str]]` | `summary` | optional |
| `authors` / `contributors` | `OnlyList[Tag[Person]]` | `author` / `contributor` | optional |
| `categories` | `OnlyList[Tag[dict]]` | `category` | optional |
| `rights` | `Optional[Tag[str]]` | `rights` | optional |
| `source` | `Optional[Tag[Source]]` | `source` | optional |

`Person`: `name` (**required**), `uri`, `email`. `Source`: `id`, `title`, `updated` (all optional).

The Atom spec requires `<updated>`, but major publishers omit it (YouTube feeds have no
feed-level `<updated>`), so it is optional here.

### RSS 1.0 (RDF) — `rss_parser.models.rdf`

In RSS 1.0 the items are siblings of the channel, not children.

`RDF`: `channel` (`Tag[RDFChannelT]`, **required**), `items` (`OnlyList[Tag[RDFItemT]]`, from
`item`), `image`, `text_input` (`textinput`).

`RDFChannel`: `title`, `link`, `description` (**required**), `image`, `text_input`.
`RDFItem`: `title`, `link` (**required**), `description`. The item's RDF identifier is
`item.attributes["rdf:about"]`; `dc:*` and `syn:*` tags are in `model_extra`.

### Podcasts — `rss_parser.models.rss.itunes`

`PodcastParser` parses into `Podcast` = `RSS[PodcastChannel[PodcastItem]]`, built from
`ITunesChannelMixin` and `ITunesItemMixin` so you can mix them into your own schema.

`ITunesChannelMixin`: `itunes_author`, `itunes_type`, `itunes_title`, `itunes_subtitle`,
`itunes_summary`, `itunes_owner` (`Tag[ITunesOwner]` with `name`/`email`), `itunes_image`
(`href` in `.attributes`), `itunes_categories` (`OnlyList[Tag[dict]]`, `text` in `.attributes`),
`itunes_explicit`, `itunes_keywords`, `itunes_new_feed_url` (`itunes:new-feed-url`),
`itunes_block`, `itunes_complete`.

`ITunesItemMixin`: `itunes_title`, `itunes_author`, `itunes_subtitle`, `itunes_summary`,
`itunes_duration` (`str` — seconds or `HH:MM:SS`), `itunes_episode` (`int`), `itunes_season`
(`int`), `itunes_episode_type` (`itunes:episodeType`), `itunes_explicit`, `itunes_image`,
`itunes_keywords`, `itunes_block`.

See [Podcasts](podcasts.md) for examples.
