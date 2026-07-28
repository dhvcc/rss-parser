# Command line interface

Installing the package also installs an `rss-parser` command. It is deliberately small: three
verbs that expose what the library *knows* — the schemas of three feed specs — and nothing else.

```bash
rss-parser validate [FILE|-]   # exit code + errors      (--json, --strict)
rss-parser parse    [FILE|-]   # faithful JSON of the model (--flat, --indent N, --ascii)
rss-parser items    [FILE|-]   # NDJSON, one item per line  (--ascii)
```

`FILE` omitted or `-` reads stdin. `python -m rss_parser <verb>` takes the same arguments, with one
difference that matters for `--schema` — see [Options on every verb](#options-on-every-verb).

## It never fetches

There is no `--url` flag and no HTTP client inside. Pipe instead:

```bash
curl -sSL https://xkcd.com/rss.xml | rss-parser validate -
```

Passing a URL is the most likely first-run mistake, so it exits 2 with that recipe instead of
trying to be clever.

Input is read as **bytes** and handed to the parser untouched, so the document's own
`<?xml encoding="..."?>` declaration decides how it is decoded.

## `validate`

The one command with no substitute: `xq`/`jq` can reshape a feed, but nothing else knows what
RSS 2.0, Atom 1.0 and RSS 1.0 require.

```console
$ rss-parser validate feed.xml
$ echo $?
0

$ rss-parser validate broken.xml
rss-parser: 1 validation error for RSS
  channel.content.link: Field required
$ echo $?
1
```

Human output goes to **stderr**, so stdout stays empty and scriptable. `--json` writes a report
to **stdout** and still sets the exit code:

```console
$ rss-parser validate --json feed.xml
{"valid": true, "feed_type": "rss", "items": 36}

$ rss-parser validate --json broken.xml
{"valid": false, "feed_type": "rss", "error": {"code": "schema_violation",
 "message": "1 validation error for RSS",
 "details": [{"loc": "channel.content.link", "type": "missing", "msg": "Field required"}]}}
```

`error.code` is one of `invalid_xml`, `unknown_feed_type`, `schema_violation`,
`entities_disabled`, `unparsed_dates`. That is where granularity lives — not in the exit code.
Because `feed_type` is reported for any parseable document, `--json` also does the job of a
`detect` subcommand.

### What validate does *not* check

It checks well-formedness, the root element, and the elements the models actually require. It is
**not** a spec conformance checker. All of these exit 0:

- a `<pubDate>` that is not a date, or a lowercase `<pubdate>`
- a misspelled tag such as `<titel>` (unknown tags are kept, not rejected)
- an Atom feed with no `<updated>`, a channel with no items
- a `<link>` that is not a URL, an `<enclosure>` with no `url`
- `<rss version="2.0"><channel/></rss>` — an entirely empty channel, with no `<title>`, `<link>`
  or `<description>` at all. Every tag's content is optional (a self-closing tag is legal), so a
  container with no children satisfies the required-field check and reports `"items": 0`.

### `--strict`

Adds the one check nothing else can do: report every **declared** date field whose value came back
as a string because it parsed as neither RFC 822 nor ISO 8601, with its path.

```console
$ rss-parser validate --strict feed.xml
rss-parser: 1 date(s) could not be parsed
  channel.items[0].pub_date: last tuesday
$ echo $?
1
```

"Declared" is the limit worth knowing: it covers the `pub_date`/`last_build_date`,
`updated`/`published` and `itunes:*` date fields the models define. It does **not** cover dates
that live in `model_extra`, which is where RSS 1.0 (RDF) keeps `dc:date` — a garbage `dc:date` on
an RDF feed still reports valid.

## `parse`

`model_dump(mode="json")` of the validated model: dates are parsed, repeatable tags are always
lists, and attributes are separated from text — none of which the raw xmltodict shape gives you.

```bash
rss-parser parse --indent 2 feed.xml
rss-parser items feed.xml | jq -r '.content.title.content'
```

`--ascii` escapes non-ASCII output for consoles that are not UTF-8. `--indent` is not
TTY-sensitive on purpose: identical bytes interactively and in a pipe are worth more than pretty
defaults.

!!! warning "`--flat` is lossy"
    `--flat` switches to `dict_plain()`, which flattens every tag to its `.content`.
    Attribute-only tags have **no content**, so `--flat` emits `null` for every `<enclosure>`,
    every Atom `<link>`, `itunes:image` and `itunes:category`:

    ```
    enclosures  default: [{"content": null, "attributes": {"url": "https://…mp3", …}}]
    enclosures  --flat:   [null]
    ```

## `items`

NDJSON: one compact JSON object per line, `\n`-terminated including the last record, flushed per
line so `| head -3` truncates immediately. Per the NDJSON spec there is no `--indent` here.

By default each record is the item's **wrapping tag**, so the tag's own `attributes` survive — that
is where RSS 1.0 keeps `rdf:about`. Fields inside the item keep their own attributes either way, so
`<guid isPermaLink="false">` is at `.content.guid.attributes.is_perma_link` in this shape.

`--flat` drops that wrapper and flattens the item itself, which is what you usually want for `jq`:

```bash
rss-parser items feed.xml         | jq -r '.content.title.content'   # lossless
rss-parser items --flat feed.xml  | jq -r '.title'                   # readable
```

`--flat` is lossy in the same two ways as `parse --flat`: the wrapping tag's attributes are gone,
and attribute-only tags such as `<enclosure>` flatten to `null`. A self-closing `<item/>` has no
content at all and comes out as `{}`.

This is the reason `items` exists rather than `xq '.rss.channel.item[]'`: xmltodict's shape is
unstable, one `<item>` yields an object and two yield an array, so the `jq` filter breaks on
single-item feeds. `OnlyList` means `rss-parser items` never does.

## Options on every verb

| flag | default | meaning |
| --- | --- | --- |
| `--parser {auto,rss,atom,rdf,podcast}` | `auto` | `auto` detects from the root element. `podcast` is the only way to get typed `itunes:*` fields, because `auto` maps `<rss>` to the plain RSS schema |
| `--schema module.path:ClassName` | — | replace the schema with a custom `XMLBaseModel` subclass |

`--schema` **executes that module's code** by design; it is never read from a file or an
environment variable. It replaces the schema, not the root key, and it is mutually exclusive with
`--parser`.

To make a module next to your feed importable, the current directory is *appended* to `sys.path`
rather than inserted, so under the `rss-parser` console script a local `json.py` cannot shadow the
standard library. That safeguard does not extend to `python -m rss_parser`: `-m` makes Python itself
put the current directory at `sys.path[0]` before any of our code runs, so a local `json.py` breaks
it the same way it breaks any other `-m` invocation. Prefer the console script in a directory you
do not control.

```bash
rss-parser parse --schema my_schemas:FeedWithDublinCore feed.xml
```

## Exit codes

| code | meaning |
| --- | --- |
| 0 | success |
| 1 | feed rejected: not well-formed, unknown root, schema violation, entities refused, or `--strict` found unparsed dates |
| 2 | usage error, unreadable input, unresolvable `--schema` |
| 141 | stdout was closed — either early (`\| head`) or before we started (`>&-`) — i.e. 128+SIGPIPE, not 1, so `set -o pipefail` scripts do not confuse it with a rejected feed |

Three main codes, matching `xmllint`, `ruff` and the W3C feed validator, all of which conflate
"malformed" with "invalid". Scripts that need the distinction read `--json`.

`--json` only ever writes a report for exit 0 and exit 1. An exit-2 condition is a problem with the
invocation, not a verdict about a feed, so stdout stays empty and the message goes to stderr —
parse stdout only when the exit code is 0 or 1. `validate --json` always reports `valid` and
`feed_type`, and reports `items` for any recognized feed (`0` for an empty one); `items` is omitted
only when `--schema` replaces the root model, because then nothing knows where the items are.

## Performance budget

There is no streaming in this version: `to_xml` materializes the whole document and
`model_validate` builds the whole tree, and both live at once. Measured on a synthetic **9.5 MB
feed with 36 709 items**:

| verb | time | peak RSS |
| --- | --- | --- |
| `validate` | 1.6 s | 264 MB (~28× the input) |
| `parse` | 2.1 s | 386 MB (~41× the input) |
| `items` | 1.5 s | 265 MB (~28× the input) |

So budget roughly **0.2 s/MB and 30–40× the input size in memory**. Real feeds are far smaller —
the largest in the test corpus is 0.21 MB / 43 ms — but do not point this at a multi-megabyte
archive feed and expect it to be cheap.
