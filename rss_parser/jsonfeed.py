"""
JSON Feed 1.1 (https://www.jsonfeed.org/version/1.1/) output.

This is lossy by design rather than by accident - see the docstrings below and
docs/cli.md for the full list of conformance decisions:

- items with no derivable id are discarded, because the spec says "any item without an id
  must be discarded" - never synthesized, since a derived id would change when a typo is fixed.
- Apple Podcasts (itunes:*) fields have no JSON Feed equivalent and are dropped silently.
- Atom ``xhtml`` text constructs cannot be safely re-serialized (xmltodict reorders mixed
  content at parse time), so they fall back to ``<summary>`` and finally to ``content_text: ""``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, NamedTuple

from rss_parser.models.atom.atom import Atom
from rss_parser.models.atom.entry import Entry
from rss_parser.models.rdf.rdf import RDF
from rss_parser.models.rss.item import Item
from rss_parser.models.rss.rss import RSS
from rss_parser.models.types.date import validate_dt_or_str
from rss_parser.models.types.tag import Tag

JSON_FEED_VERSION = "https://jsonfeed.org/version/1.1"


class JsonFeedReport(NamedTuple):
    """Counts of the lossy fallbacks ``to_json_feed`` applied while mapping a feed."""

    dropped_items: int
    "Items with no derivable id - discarded per the spec, never synthesized."

    dropped_attachments: int
    "Enclosures/links with no url or no mime type - both are required by the spec."

    unparsed_dates: int
    "Date values that never became a real datetime, so they were omitted rather than guessed."


class _Report:
    """Mutable accumulator threaded through the mapping helpers; frozen into a report at the end."""

    def __init__(self) -> None:
        self.dropped_items = 0
        self.dropped_attachments = 0
        self.unparsed_dates = 0

    def result(self) -> JsonFeedReport:
        return JsonFeedReport(self.dropped_items, self.dropped_attachments, self.unparsed_dates)


def to_json_feed(feed: Any, *, feed_url: str | None = None) -> tuple[dict[str, Any], JsonFeedReport]:
    """
    Map an ``RSS``, ``Atom``, ``RDF`` or ``Podcast`` model to a JSON Feed 1.1 document.

    ``feed_url`` is unknowable from the document itself (decision 10), so it is only set
    on the output when supplied here. Returns the document alongside a report of what was
    dropped or omitted - see :class:`JsonFeedReport`.
    """
    report = _Report()
    # isinstance, never hasattr: extra="allow" means an RDF channel's `.items` resolves to a
    # dict via model_extra, so hasattr(feed, "items") is true for the wrong reason. Podcast is
    # an RSS subclass, so it is handled by the RSS branch - itunes:* fields have no JSON Feed
    # equivalent (decision 13) and are simply never read here.
    if isinstance(feed, RSS):
        document = _map_rss(feed, report, feed_url)
    elif isinstance(feed, Atom):
        document = _map_atom(feed, report, feed_url)
    elif isinstance(feed, RDF):
        document = _map_rdf(feed, report, feed_url)
    else:
        raise TypeError(f"to_json_feed does not support {type(feed).__name__}")

    return document, report.result()


def _plain(tag: Tag | None) -> str | None:
    """
    The tag's content as plain text, or ``None`` when there is none.

    An Atom ``xhtml`` text construct has a ``dict`` content (decision 4) - never a safe string -
    so this returns ``None`` for it too, which is what lets callers fall back cleanly.
    """
    if tag is None or tag.content is None:
        return None
    return tag.content if isinstance(tag.content, str) else None


def _int_or_none(value: Any) -> int | None:
    """``int(value)``, or ``None`` for anything that is not one - e.g. ``length=""`` (github-49)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _date(tag: Tag | None, report: _Report) -> str | None:
    """
    A declared ``DateTimeOrStr`` field as an RFC 3339-ish string, or ``None``.

    Only a real ``datetime`` is emitted (decision 6); a value the library kept as a raw string
    is counted in ``unparsed_dates`` instead. Naive datetimes come out of ``isoformat()``
    without an offset, which is not strictly RFC 3339 - that happens for feeds that omit the zone.
    """
    if tag is None or tag.content is None:
        return None
    if isinstance(tag.content, datetime):
        return tag.content.isoformat()
    report.unparsed_dates += 1
    return None


def _extra_date(raw: Any, report: _Report) -> str | None:
    """Like :func:`_date`, but for a raw string living in ``model_extra`` (RDF's ``dc:date``)."""
    if raw is None:
        return None
    value = validate_dt_or_str(raw)
    if isinstance(value, datetime):
        return value.isoformat()
    report.unparsed_dates += 1
    return None


class _ItemFields(NamedTuple):
    """Everything about one item except its id - bundled so ``_finalize_item`` takes two args."""

    url: str | None
    title: str | None
    content: dict[str, str]
    summary: str | None
    date_published: str | None
    date_modified: str | None
    authors: list[dict[str, str]] | None
    tags: list[str] | None
    attachments: list[dict[str, Any]]


def _finalize_item(item_id: str, fields: _ItemFields) -> dict[str, Any]:
    """Assemble one JSON Feed item in the field order the contract specifies. ``item_id`` is truthy - callers drop id-less items themselves and count them."""  # noqa: E501
    record: dict[str, Any] = {"id": item_id}
    if fields.url:
        record["url"] = fields.url
    if fields.title:
        record["title"] = fields.title
    record.update(fields.content)
    if fields.summary:
        record["summary"] = fields.summary
    if fields.date_published:
        record["date_published"] = fields.date_published
    if fields.date_modified:
        record["date_modified"] = fields.date_modified
    if fields.authors:
        record["authors"] = fields.authors
    if fields.tags:
        record["tags"] = fields.tags
    if fields.attachments:
        record["attachments"] = fields.attachments
    return record


class _FeedMeta(NamedTuple):
    """Feed-level metadata, bundled so ``_document`` takes two args."""

    title: str | None
    home_page_url: str | None
    feed_url: str | None
    description: str | None
    language: str | None


def _document(meta: _FeedMeta, items: list[dict[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {"version": JSON_FEED_VERSION, "title": meta.title or ""}
    if meta.home_page_url:
        document["home_page_url"] = meta.home_page_url
    if meta.feed_url:
        # Unknowable from the document itself (decision 10) - only set when the caller supplies it.
        document["feed_url"] = meta.feed_url
    if meta.description:
        document["description"] = meta.description
    if meta.language:
        document["language"] = meta.language
    document["items"] = items
    return document


# --- RSS (and Podcast) --------------------------------------------------------------------


def _rss_item_id(item: Item) -> str | None:
    """``<guid>`` first, then the first ``<link>`` - never synthesized (decision 1)."""
    if item.guid is not None and item.guid.content:
        return item.guid.content
    for link in item.links:
        if link.content:
            return link.content
    return None


def _rss_attachments(item: Item, report: _Report) -> list[dict[str, Any]]:
    attachments = []
    for enclosure in item.enclosures:
        url = enclosure.attributes.get("url")
        mime_type = enclosure.attributes.get("type")
        if not url or not mime_type:
            report.dropped_attachments += 1
            continue
        attachment: dict[str, Any] = {"url": url, "mime_type": mime_type}
        size = _int_or_none(enclosure.attributes.get("length"))
        if size is not None:
            attachment["size_in_bytes"] = size
        attachments.append(attachment)
    return attachments


def _dc_creator(model) -> str | None:
    """
    Dublin Core is how most feeds actually name a person: RSS ``<author>`` is item-level and
    nearly extinct, while ``dc:creator`` carries the byline on Slashdot, Hacker News and NPR.
    It is not a declared field, so it arrives in ``model_extra`` under its literal XML key.
    """
    value = (getattr(model, "model_extra", None) or {}).get("dc:creator")
    return value if isinstance(value, str) and value else None


def _authors_from_name(name: str | None) -> list[dict[str, str]] | None:
    return [{"name": name}] if name else None


def _rss_authors(item: Item) -> list[dict[str, str]] | None:
    """
    RSS ``<author>`` is defined as an email address, but publishers put names there - either
    way it goes in ``name``, since JSON Feed's author object has no email member (decision 7).
    ``dc:creator`` is the fallback, and in practice the more common one.
    """
    author = item.author.content if item.author is not None else None
    return _authors_from_name(author or _dc_creator(item))


def _rss_tags(categories) -> list[str] | None:
    """Plain strings - the ``domain`` attribute is dropped (decision 8)."""
    tags = [category.content for category in categories if category.content]
    return tags or None


def _extra_tags(value) -> list[str] | None:
    """``dc:subject`` is how RSS 1.0 categorises: one string, or a list when repeated."""
    if isinstance(value, str):
        return [value] if value else None
    if isinstance(value, list):
        tags = [item for item in value if isinstance(item, str) and item]
        return tags or None
    return None


def _rss_item(item_tag: Tag, report: _Report) -> dict[str, Any] | None:
    item = item_tag.content
    if item is None:
        return None
    item_id = _rss_item_id(item)
    if item_id is None:
        report.dropped_items += 1
        return None
    content = {"content_html": item.description.content} if item.description and item.description.content else {}
    if not content:
        content = {"content_text": ""}
    return _finalize_item(
        item_id,
        _ItemFields(
            url=next((link.content for link in item.links if link.content), None),
            title=_plain(item.title),
            content=content,
            summary=None,
            date_published=_date(item.pub_date, report),
            date_modified=None,
            authors=_rss_authors(item),
            tags=_rss_tags(item.categories),
            attachments=_rss_attachments(item, report),
        ),
    )


def _map_rss(feed: RSS, report: _Report, feed_url: str | None) -> dict[str, Any]:
    channel = feed.channel.content
    if channel is None:
        return _document(_FeedMeta(None, None, feed_url, None, None), [])

    items = []
    for item_tag in channel.items:
        item = _rss_item(item_tag, report)
        if item is not None:
            items.append(item)

    meta = _FeedMeta(
        title=_plain(channel.title),
        home_page_url=_plain(channel.link),
        feed_url=feed_url,
        description=_plain(channel.description),
        language=_plain(channel.language),
    )
    return _document(meta, items)


# --- Atom ----------------------------------------------------------------------------------


def _atom_construct(tag: Tag | None) -> dict[str, str] | None:
    """
    Route an Atom text construct on its ``type`` (decision 4): absent/``text`` -> ``content_text``,
    ``html`` -> ``content_html``. ``xhtml`` content is a mapping, so ``_plain`` already returns
    ``None`` for it, which is what lets the caller fall back to ``<summary>``.
    """
    text = _plain(tag)
    if text is None or tag is None:  # tag is not None here - _plain(None) already returned None above
        return None
    if tag.attributes.get("type") == "html":
        return {"content_html": text}
    return {"content_text": text}


def _atom_link(links, rel: str) -> str | None:
    for link in links:
        if link.attributes.get("rel") == rel:
            href = link.attributes.get("href")
            if href:
                return href
    return None


def _atom_attachments(links, report: _Report) -> list[dict[str, Any]]:
    """``<link rel="enclosure">`` is Atom's equivalent of an RSS ``<enclosure>``."""
    attachments = []
    for link in links:
        if link.attributes.get("rel") != "enclosure":
            continue
        url = link.attributes.get("href")
        mime_type = link.attributes.get("type")
        if not url or not mime_type:
            report.dropped_attachments += 1
            continue
        attachment: dict[str, Any] = {"url": url, "mime_type": mime_type}
        size = _int_or_none(link.attributes.get("length"))
        if size is not None:
            attachment["size_in_bytes"] = size
        attachments.append(attachment)
    return attachments


def _atom_authors(authors) -> list[dict[str, str]] | None:
    """``Person.name`` -> ``name``, ``Person.uri`` -> ``url`` (decision 7)."""
    result = []
    for author_tag in authors:
        person = author_tag.content
        if person is None:
            continue
        author: dict[str, str] = {}
        if person.name is not None and person.name.content:
            author["name"] = person.name.content
        if person.uri is not None and person.uri.content:
            author["url"] = person.uri.content
        if author:
            result.append(author)
    return result or None


def _atom_tags(categories) -> list[str] | None:
    tags = [category.attributes.get("term") for category in categories if category.attributes.get("term")]
    return tags or None


def _atom_content_and_summary(entry: Entry) -> tuple[dict[str, str], str | None]:
    """
    ``<content>`` is the primary source; ``<summary>`` is used as a fallback only when
    ``<content>`` is absent or unusable (decisions 3, 4, 14). When ``<content>`` *is* usable,
    ``<summary>`` is reported separately as the item's ``summary`` rather than folded into it.
    """
    primary = _atom_construct(entry.content)
    if primary is not None:
        return primary, _plain(entry.summary)
    fallback = _atom_construct(entry.summary)
    if fallback is not None:
        return fallback, None
    return {"content_text": ""}, None


def _atom_entry(entry_tag: Tag, report: _Report) -> dict[str, Any] | None:
    entry = entry_tag.content
    if entry is None:
        return None
    item_id = entry.id.content if entry.id is not None else None
    if not item_id:
        report.dropped_items += 1
        return None
    content, summary = _atom_content_and_summary(entry)
    return _finalize_item(
        item_id,
        _ItemFields(
            url=_atom_link(entry.links, "alternate"),
            title=_plain(entry.title),
            content=content,
            summary=summary,
            date_published=_date(entry.published, report),
            date_modified=_date(entry.updated, report),
            authors=_atom_authors(entry.authors),
            tags=_atom_tags(entry.categories),
            attachments=_atom_attachments(entry.links, report),
        ),
    )


def _map_atom(atom: Atom, report: _Report, feed_url: str | None) -> dict[str, Any]:
    feed = atom.feed.content
    if feed is None:
        return _document(_FeedMeta(None, None, feed_url, None, None), [])

    items = []
    for entry_tag in feed.entries:
        entry = _atom_entry(entry_tag, report)
        if entry is not None:
            items.append(entry)

    meta = _FeedMeta(
        title=_plain(feed.title),
        home_page_url=_atom_link(feed.links, "alternate"),
        feed_url=feed_url,
        description=_plain(feed.subtitle),
        language=atom.feed.attributes.get("xml:lang"),
    )
    return _document(meta, items)


# --- RDF (RSS 1.0) ---------------------------------------------------------------------------


def _rdf_item_id(item_tag: Tag) -> str | None:
    """``rdf:about`` lives on the wrapping tag's attributes, not on the item model itself."""
    about = item_tag.attributes.get("rdf:about")
    if about:
        return about
    item = item_tag.content
    if item is not None and item.link is not None and item.link.content:
        return item.link.content
    return None


def _rdf_item(item_tag: Tag, report: _Report) -> dict[str, Any] | None:
    item = item_tag.content
    if item is None:
        return None
    item_id = _rdf_item_id(item_tag)
    if item_id is None:
        report.dropped_items += 1
        return None
    content = {"content_html": item.description.content} if item.description and item.description.content else {}
    if not content:
        content = {"content_text": ""}
    extra = item.model_extra or {}
    return _finalize_item(
        item_id,
        _ItemFields(
            url=item.link.content if item.link else None,
            title=_plain(item.title),
            content=content,
            summary=None,
            date_published=_extra_date(extra.get("dc:date"), report),
            date_modified=None,
            authors=_authors_from_name(_dc_creator(item)),
            tags=_extra_tags(extra.get("dc:subject")),
            attachments=[],
        ),
    )


def _map_rdf(rdf: RDF, report: _Report, feed_url: str | None) -> dict[str, Any]:
    channel = rdf.channel.content
    items = []
    for item_tag in rdf.items:
        item = _rdf_item(item_tag, report)
        if item is not None:
            items.append(item)

    if channel is None:
        return _document(_FeedMeta(None, None, feed_url, None, None), items)

    extra = channel.model_extra or {}
    meta = _FeedMeta(
        title=_plain(channel.title),
        home_page_url=_plain(channel.link),
        feed_url=feed_url,
        description=_plain(channel.description),
        language=extra.get("dc:language"),
    )
    return _document(meta, items)


__all__ = ("JsonFeedReport", "to_json_feed")
