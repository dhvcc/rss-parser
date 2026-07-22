# Migration

## 3.x -> 4.0

### Breaking changes

**Legacy pydantic v1 models are gone.** `rss_parser.models.legacy` and
`rss_parser.pydantic_proxy` have been removed. 4.x requires pydantic >= 2.7.
If you still need pydantic v1, stay on `rss-parser==3.x`.

**Item elements are optional now (spec-compliant).** Per the RSS 2.0 spec, all elements of an
`<item>` are optional as long as `title` *or* `description` is present. `item.title`,
`item.description` and `item.links` used to be required — code assuming they're always set
should check for `None` (feeds that used to fail validation now parse).

**Fixed channel fields** (these were wrong/broken in 3.x):

| Field | 3.x | 4.0 |
| --- | --- | --- |
| `channel.text_input` | `Tag[str]` (crashed on valid feeds) | `Tag[TextInput]` |
| `channel.rating` | `Tag[TextInput]` | `Tag[str]` |
| `channel.skip_hours` | `Tag[str]` (crashed on valid feeds) | `Tag[SkipHours]` (`.hours` list of ints) |
| `channel.skip_days` | `Tag[str]` (crashed on valid feeds) | `Tag[SkipDays]` (`.days` list of strs) |
| `channel.managing_editor` | *missing* | `Tag[str]` |
| `channel.ttl` | `Tag[str]` | `Tag[int]` |
| `item.pub_date` | `Tag[str]` | `Tag[DateTimeOrStr]` |

**Mixin classes were flattened.** `RequiredChannelElementsMixin`, `OptionalChannelElementsMixin`,
`RequiredItemElementsMixin`, `OptionalItemElementsMixin` and the Atom equivalents no longer exist —
the fields live directly on `Channel`, `Item`, `Feed`, `Entry`. Subclass those instead.

**`atom.Entry.source`** is now a typed `Tag[Source]` instead of `Tag[str]`.

**Atom `updated` is optional.** The spec requires it, but major real-world publishers omit it
(YouTube feeds have no feed-level `<updated>`), so `Feed.updated` and `Entry.updated` can be `None`.

**Malformed XML raises `InvalidXMLError`** (a `ValueError` subclass) instead of leaking
xmltodict's `ExpatError`. The original error is available as `__cause__`.

**`Tag.flatten_tag_encoder` was removed.** It was the implementation detail behind
`json_plain()`/`dict_plain()`, which are now implemented properly (in 3.x they silently
returned the *unflattened* structure - this is also fixed).

**Unknown tags are kept.** Models now use pydantic's `extra="allow"`, so undeclared tags
(e.g. `itunes:*` on the plain RSS schema) show up in `model_dump()` output and in `model_extra`
instead of being dropped.

**`str(tag)` returns the content.** `print(feed.channel.title)` prints `Some title` instead of
`content='Some title' attributes={}`. Reprs are unchanged.

### New in 4.0

- `parse()` — universal entry point with feed type detection, plus `detect_feed_type()`,
  `FeedType` and `UnknownFeedTypeError`. See [Parsing feeds](parsing.md).
- RSS 1.0 (RDF) support: `RDFParser` and `rss_parser.models.rdf`.
- Typed podcast support: `PodcastParser`, `Podcast`, and the iTunes mixins.
  See [Podcasts](podcasts.md).
- Generic models: `RSS[Channel[MyItem]]` replaces the subclass-everything dance.
  See [Customizing the schema](extending.md).
- Custom schemas need one subclass instead of three; see the field types cheat sheet in
  [Customizing the schema](extending.md#field-types-cheat-sheet).

## 2.x -> 3.0

`rss-parser` 3.x upgraded the runtime models to pydantic v2:

- Models inherit from pydantic v2 `BaseModel` — use `model_dump()`/`model_dump_json()`
  instead of `dict()`/`json()`.
- List-like XML fields use `OnlyList[...]` with an automatic `default_factory`,
  so they are always lists.

## 1.x -> 2.0

- The `Parser` class was renamed to `RSSParser`.
- RSS-specific models moved from `rss_parser.models` to `rss_parser.models.rss`.
- Date parsing produces `datetime` objects where it previously kept strings.
