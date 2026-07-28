# Security Policy

`rss-parser` is a Python library that parses untrusted XML from the network, so input-handling
issues are in scope.

## Supported versions

| Version | Supported |
| --- | --- |
| 4.x | Yes — fixes land in the latest 4.x release |
| 3.x | No — upgrade, see the [migration guide](https://dhvcc.github.io/rss-parser/migration/) |
| <= 2.x | No |

## Reporting a vulnerability

Email **1337kwiz@gmail.com** with `rss-parser security` in the subject. Please include:

- the affected version (`pip show rss-parser`) and Python version,
- a minimal feed or XML snippet that reproduces the problem,
- what happens and what you expected instead.

Do not open a public issue for a suspected vulnerability. Expect an acknowledgement within a
few days; fixes are released as a new patch version on PyPI and credited in the release notes
unless you ask otherwise.

## Scope

In scope: crashes, hangs, unbounded memory growth, or entity/external-reference handling
triggered by parsing a feed with this library.

### Current XML hardening

`rss-parser` parses with [xmltodict](https://github.com/martinblech/xmltodict), which runs with
`disable_entities=True`. Any DTD entity declaration is refused before expansion, so both
external-entity (XXE) and entity-expansion ("billion laughs") feeds are rejected rather than
processed — verified against 4.x:

```python
RSSParser.parse(feed_with_entity_declaration)
# EntitiesDisabledError: entities are disabled
```

`EntitiesDisabledError` subclasses `ValueError` but deliberately **not** `InvalidXMLError`, since
such a document is well-formed XML and is refused rather than malformed. Before 4.3.0 this was a
bare `ValueError` from xmltodict with the same message, so `except ValueError` keeps working.
There is no built-in limit on document size or nesting depth — cap the response size yourself
before parsing feeds you do not control.

Out of scope, and deliberately so:

- **Feed content is returned as-is.** HTML in `<description>`/`<content>` (usually CDATA) is
  never sanitized — escaping it before rendering is the caller's job. See
  [How XML is handled](https://dhvcc.github.io/rss-parser/xml/).
- Vulnerabilities in dependencies ([pydantic](https://github.com/pydantic/pydantic),
  [xmltodict](https://github.com/martinblech/xmltodict), and the standard library's
  `xml.parsers.expat`) — report those upstream; open an issue here if this library needs a
  version bump to pick up a fix.
