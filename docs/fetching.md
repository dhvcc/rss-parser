# Fetching feeds from a URL

`rss-parser` parses feeds you already have as a string. It never touches the network, so there is
no `parseURL`/`parseString` and no HTTP options to configure — you pick the HTTP client, the
timeouts and the caching policy, and hand the body to `parse()`.

!!! note "Looking for `parseURL`?"
    That is the API of the **npm** package also called `rss-parser`. This is the Python package
    (`pip install rss-parser`, imported as `rss_parser`); the equivalent is two lines:

    ```python
    import requests
    from rss_parser import parse

    feed = parse(requests.get(url, timeout=10).text)
    ```

## requests

```python
import requests
from rss_parser import parse

response = requests.get(
    "https://rss.art19.com/apology-line",
    timeout=10,
    headers={"User-Agent": "my-app/1.0 (+https://example.com)"},
)
response.raise_for_status()

feed = parse(response.text)
print(feed.channel.title)
```

!!! warning "Pass a `str`, decode bytes yourself"
    `parse()` expects text. Handing it `bytes` does **not** decode them — the value is stringified,
    so `b'<?xml ...'` becomes the literal text `"b'<?xml ...'"` and you get `InvalidXMLError`.

    ```python
    feed = parse(response.content.decode("utf-8"))   # explicit and safe
    feed = parse(response.content)                   # InvalidXMLError
    ```

    `response.text` uses the charset the server advertised, which feed hosts often get wrong. When
    it produces mojibake, decode by the feed's own declaration instead:

    ```python
    response.encoding = response.apparent_encoding
    feed = parse(response.text)
    ```

## httpx (sync and async)

```python
import httpx
from rss_parser import parse

with httpx.Client(timeout=10, follow_redirects=True) as client:
    feed = parse(client.get(url).text)
```

```python
import asyncio
import httpx
from rss_parser import parse


async def fetch_feeds(urls):
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        responses = await asyncio.gather(*(client.get(url) for url in urls))
    return [parse(response.text) for response in responses]
```

Parsing is CPU-bound and synchronous — run `parse()` after the awaits, or push it into
`asyncio.to_thread` if a feed is big enough to matter.

## Many sources at once

`parse()` detects the type per document, so a mixed list of RSS, Atom and RDF URLs needs no
branching to *parse* — only to *read*, because the models follow their own specs:

```python
from rss_parser import parse
from rss_parser.models.rss import RSS
from rss_parser.models.atom import Atom
from rss_parser.models.rdf import RDF


def entries(feed):
    """Yield (id, title, link, published) for any supported feed type."""
    if isinstance(feed, RSS):
        for item in feed.channel.items:
            link = str(item.links[0]) if item.links else None
            yield str(item.guid or link), str(item.title), link, item.pub_date
    elif isinstance(feed, Atom):
        for entry in feed.feed.entries:
            link = str(entry.links[0]) if entry.links else None
            yield str(entry.id), str(entry.title), link, entry.published or entry.updated
    elif isinstance(feed, RDF):
        for item in feed.items:
            yield str(item.link), str(item.title), str(item.link), None
```

The per-format field names are in the [API reference](reference.md#feed-models).

| | RSS 2.0 | Atom 1.0 | RSS 1.0 (RDF) |
| --- | --- | --- | --- |
| Feed metadata | `feed.channel` | `feed.feed` | `feed.channel` |
| Items | `feed.channel.items` | `feed.feed.entries` | `feed.items` |
| Stable id | `item.guid` (fall back to `item.links[0]`) | `entry.id` | `item.attributes["rdf:about"]` or `item.link` |
| Link | `item.links[0]` | `entry.links[0]` | `item.link` |
| Timestamp | `item.pub_date` | `entry.published` / `entry.updated` | `dc:date` via `model_extra` |

## Polling and deduplication

Feeds repeat their items on every fetch, so a poller needs a stable key per item. In RSS that is
`<guid>` when present, otherwise the link; in Atom it is the required `<id>`:

```python
from rss_parser import parse

seen: set[str] = set()


def new_items(xml: str):
    feed = parse(xml)
    for item in feed.channel.items:
        key = str(item.guid) if item.guid else str(item.links[0])
        if key in seen:
            continue
        seen.add(key)
        yield item
```

Two things worth knowing before you trust a key:

- `<guid isPermaLink="false">` is common; the flag lives in `item.guid.attributes["is_perma_link"]`.
  Treat the value as an opaque string either way.
- Publishers rewrite `<title>` and `<description>` in place without changing the guid. If you need
  to notice edits, hash the fields you care about alongside the key.

```python
from hashlib import sha256


def content_fingerprint(item) -> str:
    payload = "\x00".join(str(field or "") for field in (item.title, item.description, item.pub_date))
    return sha256(payload.encode()).hexdigest()
```

### Don't refetch unchanged feeds

Feed hosts support conditional GET. Keep the validators per feed and you turn most polls into a
304 with no body to parse:

```python
import requests
from rss_parser import parse

state: dict[str, dict[str, str]] = {}


def poll(url: str):
    headers = {}
    cached = state.get(url, {})
    if "etag" in cached:
        headers["If-None-Match"] = cached["etag"]
    if "last_modified" in cached:
        headers["If-Modified-Since"] = cached["last_modified"]

    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 304:
        return None

    response.raise_for_status()
    validators = {}
    if "ETag" in response.headers:
        validators["etag"] = response.headers["ETag"]
    if "Last-Modified" in response.headers:
        validators["last_modified"] = response.headers["Last-Modified"]
    state[url] = validators

    return parse(response.text)
```

Also honour the feed's own hints when it sets them: `channel.ttl` (minutes),
`channel.skip_hours.content.hours` and `channel.skip_days.content.days`.

### Keeping custom fields through deduplication

Tags that are not on the schema are not dropped — they stay in `model_extra`, so a dedup key or a
downstream record can use them without a custom schema:

```python
item = feed.channel.items[0].content
item.model_extra.get("dc:creator")
item.model_extra.get("content:encoded")
```

If you rely on such a field, declare it instead — you get validation and autocomplete. See
[Customizing the schema](extending.md).

## Next steps

- [API reference](reference.md) — every parser, model and field in one place.
- [Error handling](parsing.md#error-handling) — what each failure raises.
- [Customizing the schema](extending.md) — typed access to namespaced tags.
