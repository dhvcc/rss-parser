# Real-world feed corpus

Real feeds captured from the wild on 2026-07-23, committed as-is (bytes untouched) so the
suite runs offline and deterministically. The one exception: `podcast/lex_fridman` was
truncated to its first 5 items (the full feed is ~2MB); the closing tags were re-added by hand.

Each feed dir contains:

- `data.xml` — the raw captured feed
- `expect.json` — expectations **derived by inspecting the raw XML**, not by running the
  parser. This is what keeps the corpus honest: the parser is checked against the document,
  not against itself.

`expect.json` fields: `type` (detected feed type), `version` (RSS only), `title`,
`items` (count), `first_item_title`, optional `encoding` (when not utf-8, e.g. slashdot is
iso-8859-1) and per-feed spot facts (e.g. `itunes_author`).

| Feed | Source | Notes |
| --- | --- | --- |
| rss/bbc_news | https://feeds.bbci.co.uk/news/rss.xml | media:\*, dc:\* namespaces |
| rss/heise | https://www.heise.de/rss/heise.rdf | RSS 2.0 despite the .rdf URL; German umlauts; 153 items |
| rss/hnrss | https://hnrss.org/frontpage | dc:creator, comments |
| rss/npr | https://feeds.npr.org/1001/rss.xml | npr:\*, content:encoded |
| rss/xkcd_rss | https://xkcd.com/rss.xml | minimal feed |
| atom/cpython_releases | https://github.com/python/cpython/releases.atom | GitHub-flavored Atom |
| atom/theverge | https://www.theverge.com/rss/index.xml | Atom despite the /rss/ URL |
| atom/xkcd_atom | https://xkcd.com/atom.xml | minimal feed |
| atom/youtube | https://www.youtube.com/feeds/videos.xml?channel_id=UC_x5XG1OV2P6uZZ5FSM9Ttw | **violates Atom spec**: no feed-level `<updated>`; yt:\*, media:\* |
| rdf/slashdot | https://rss.slashdot.org/Slashdot/slashdotMain | real RSS 1.0 (RDF), ISO-8859-1 encoded |
| podcast/lex_fridman | https://lexfridman.com/feed/podcast/ | itunes:\* tags, CDATA, truncated to 5 items |

To add a feed: create `corpus/<kind>/<name>/data.xml`, write `expect.json` by reading the
XML yourself, done — the test discovers it automatically.
