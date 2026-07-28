"""
JSON Feed 1.1 conformance suite.

Every assertion here is derived from the normative language of the published spec
(https://www.jsonfeed.org/version/1.1/) - not from ``rss_parser/jsonfeed.py``'s own docstrings
or from the 4.4.0 contract's "settled decisions". If a feed anywhere in tests/samples/** or
tests/corpus/** produces output that violates the spec, that is a bug in the mapper, and the
fix belongs in rss_parser/jsonfeed.py, not in this file.

Parametrized over every feed in the tree (``iter_samples()`` + ``iter_corpus()``), so a feed
added later is covered automatically.
"""

import json
import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, List, Tuple

import pytest

from rss_parser import to_json_feed
from rss_parser.jsonfeed import JsonFeedReport
from rss_parser.models.atom import Atom
from rss_parser.models.rss import RSS
from tests.conftest import PARSERS_BY_KIND, iter_corpus, iter_samples

FEEDS: List[Tuple[str, str, Path]] = [("samples", kind, feed_dir) for kind, feed_dir in iter_samples()] + [
    ("corpus", kind, feed_dir) for kind, feed_dir in iter_corpus()
]
FEED_IDS = [f"{source}/{kind}/{feed_dir.name}" for source, kind, feed_dir in FEEDS]

# The real JSON Feed 1.1 field vocabulary (https://www.jsonfeed.org/version/1.1/), used to spot
# any emitted field that isn't spec-blessed and isn't an underscore-prefixed extension. "author"
# (singular) is kept for backwards compatibility with JSON Feed 1.0.
FEED_LEVEL_SPEC_FIELDS = {
    "version",
    "title",
    "home_page_url",
    "feed_url",
    "description",
    "user_comment",
    "next_url",
    "icon",
    "favicon",
    "authors",
    "author",
    "language",
    "expired",
    "hubs",
    "items",
}
ITEM_LEVEL_SPEC_FIELDS = {
    "id",
    "url",
    "external_url",
    "title",
    "content_html",
    "content_text",
    "summary",
    "image",
    "banner_image",
    "date_published",
    "date_modified",
    "authors",
    "author",
    "tags",
    "attachments",
    "language",
}

JSON_LEAF_TYPES = (str, int, float, bool, type(None))


def get_source_items(feed) -> list:
    """The *source* items/entries, before jsonfeed mapping - mirrors test_corpus.py's get_items()."""
    if isinstance(feed, RSS):
        return feed.channel.content.items
    if isinstance(feed, Atom):
        return feed.feed.content.entries
    return feed.items  # RDF


@lru_cache(maxsize=None)
def _load(source: str, kind: str, feed_dir: Path):
    """Parse a feed and run the default (no feed_url) jsonfeed mapping, once per feed."""
    data = (feed_dir / "data.xml").read_bytes()  # let the parser honor the doc's own <?xml encoding?>
    feed = PARSERS_BY_KIND[kind].parse(data)
    doc, report = to_json_feed(feed)
    return feed, doc, report


def find_nulls(value: Any, path: str = "") -> Iterator[str]:
    """Yield a path-like locator for every literal ``None`` found anywhere in a nested structure."""
    if value is None:
        yield path or "<root>"
    elif isinstance(value, dict):
        for key, sub in value.items():
            yield from find_nulls(sub, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            yield from find_nulls(sub, f"{path}[{i}]")


def find_non_json_types(value: Any, path: str = "<root>") -> Iterator[str]:
    """Yield a description for every value that isn't a plain JSON-native type."""
    if isinstance(value, dict):
        for key, sub in value.items():
            if not isinstance(key, str):
                yield f"{path} key {key!r} is not a string"
            yield from find_non_json_types(sub, f"{path}.{key}")
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            yield from find_non_json_types(sub, f"{path}[{i}]")
    elif isinstance(value, JSON_LEAF_TYPES):
        if isinstance(value, float) and not math.isfinite(value):
            yield f"{path}: non-finite float {value!r}"
    else:
        yield f"{path}: non-JSON type {type(value).__name__} ({value!r})"


class TestFeedLevelRequiredFields:
    """Spec: version and title are the two required top-level fields."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_version_is_exactly_1_1(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        assert (
            doc.get("version") == "https://jsonfeed.org/version/1.1"
        ), f"{source}/{kind}/{feed_dir.name}: version={doc.get('version')!r}"

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_title_is_present(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        assert (
            isinstance(doc.get("title"), str) and doc["title"]
        ), f"{source}/{kind}/{feed_dir.name}: title={doc.get('title')!r}"


class TestItemId:
    """Spec: "any item without an id must be discarded" - so every *emitted* item must have one."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_every_item_has_a_nonempty_string_id(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            item_id = item.get("id")
            assert isinstance(item_id, str) and item_id, (
                f"{source}/{kind}/{feed_dir.name} item[{i}]: id={item_id!r} - the spec requires items "
                "without an id to be discarded, so a null/missing/empty id must never be emitted"
            )

    def test_rss_0_91_description_only_item_is_dropped_not_emitted_with_a_null_id(self):
        """The one documented drop case in the whole tree: no guid, no link - nothing to key an id on."""
        _, doc, report = _load("samples", "rss", next(d for s, k, d in FEEDS if k == "rss" and d.name == "rss_0_91"))

        assert report.dropped_items >= 1, f"expected at least 1 dropped item, report={report!r}"
        assert all(item.get("id") for item in doc["items"]), "no emitted item may have a falsy id"


class TestItemContent:
    """Spec: "content_html and content_text are each optional strings - but one or both must be present"."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_every_item_has_content_html_or_content_text(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            assert "content_html" in item or "content_text" in item, (
                f"{source}/{kind}/{feed_dir.name} item[{i}] (id={item.get('id')!r}): "
                "neither content_html nor content_text is present"
            )

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_content_fields_are_strings_when_present(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            for field in ("content_html", "content_text"):
                if field in item:
                    assert isinstance(
                        item[field], str
                    ), f"{source}/{kind}/{feed_dir.name} item[{i}].{field}={item[field]!r} is not a string"


class TestAuthors:
    """Spec: authors is "an array" of author objects; "if you provide an author object, then at least
    one is required" (name/url/avatar) - and there is no string form of an author, at feed or item level.
    """

    @staticmethod
    def _assert_valid_authors_array(authors, where: str) -> None:
        assert isinstance(authors, list), f"{where}: authors is not an array: {authors!r}"
        assert authors, f"{where}: authors is present but empty"
        for j, author in enumerate(authors):
            assert isinstance(author, dict), f"{where} authors[{j}]={author!r}: authors are objects, never bare strings"
            assert any(
                k in author for k in ("name", "url", "avatar")
            ), f"{where} authors[{j}]={author!r}: has none of name/url/avatar"

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_feed_level_authors_when_present(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        if "authors" in doc:
            self._assert_valid_authors_array(doc["authors"], f"{source}/{kind}/{feed_dir.name}")

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_item_level_authors_when_present(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            if "authors" in item:
                self._assert_valid_authors_array(
                    item["authors"], f"{source}/{kind}/{feed_dir.name} item[{i}] (id={item.get('id')!r})"
                )

    def test_rss_author_email_field_becomes_a_name_not_an_email_object(self):
        """github-49's <author> holds a human name, not an email - JSON Feed authors have no email member."""
        feed_dir = next(d for s, k, d in FEEDS if k == "rss" and d.name == "github-49")
        _, doc, _ = _load("samples", "rss", feed_dir)

        items_with_authors = [item for item in doc["items"] if "authors" in item]
        assert items_with_authors, "samples/rss/github-49 has <author> on every item - expected authors present"
        for item in items_with_authors:
            for author in item["authors"]:
                assert "email" not in author, f"item {item.get('id')!r}: author has an email member: {author!r}"


class TestTags:
    """Spec: tags is "an array" whose members are plain text - i.e. strings only."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_tags_are_strings_only(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            tags = item.get("tags")
            if tags is None:
                continue
            assert isinstance(tags, list), f"{source}/{kind}/{feed_dir.name} item[{i}]: tags={tags!r}"
            for j, tag in enumerate(tags):
                assert isinstance(
                    tag, str
                ), f"{source}/{kind}/{feed_dir.name} item[{i}].tags[{j}]={tag!r} is not a string"


class TestAttachments:
    """Spec: attachments each require "url" and "mime_type"; size_in_bytes/duration_in_seconds are numbers."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_attachments_shape_when_present(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            attachments = item.get("attachments")
            if attachments is None:
                continue

            assert (
                isinstance(attachments, list) and attachments
            ), f"{source}/{kind}/{feed_dir.name} item[{i}]: attachments={attachments!r}"
            for j, attachment in enumerate(attachments):
                where = f"{source}/{kind}/{feed_dir.name} item[{i}].attachments[{j}]"

                url = attachment.get("url")
                assert isinstance(url, str) and url, f"{where}: url={url!r}"

                mime_type = attachment.get("mime_type")
                assert isinstance(mime_type, str) and mime_type, f"{where}: mime_type={mime_type!r}"

                if "size_in_bytes" in attachment:
                    size = attachment["size_in_bytes"]
                    assert isinstance(size, int) and not isinstance(size, bool), f"{where}: size_in_bytes={size!r}"

                if "duration_in_seconds" in attachment:
                    duration = attachment["duration_in_seconds"]
                    assert isinstance(duration, (int, float)) and not isinstance(
                        duration, bool
                    ), f"{where}: duration_in_seconds={duration!r}"

    def test_apology_line_enclosure_lengths_become_real_ints(self):
        """samples/podcast/apology_line has literal numeric `length` attributes - the easy case."""
        feed_dir = next(d for s, k, d in FEEDS if k == "podcast" and d.name == "apology_line")
        _, doc, _ = _load("samples", "podcast", feed_dir)

        items_with_attachments = [item for item in doc["items"] if item.get("attachments")]
        assert items_with_attachments, "samples/podcast/apology_line has <enclosure> on every item"
        for item in items_with_attachments:
            for attachment in item["attachments"]:
                assert isinstance(attachment["size_in_bytes"], int)

    def test_github_49_blank_length_attribute_is_omitted_not_int_cast(self):
        """samples/rss/github-49 has <enclosure length="" .../> - url and mime_type both present, so the
        attachment must still be emitted, just without a fabricated size_in_bytes.
        """
        feed_dir = next(d for s, k, d in FEEDS if k == "rss" and d.name == "github-49")
        _, doc, _ = _load("samples", "rss", feed_dir)

        first_item = doc["items"][0]
        assert "attachments" in first_item, f"item {first_item.get('id')!r}: expected an attachment"
        attachment = first_item["attachments"][0]
        assert attachment["mime_type"] == "image/png", attachment
        assert (
            "size_in_bytes" not in attachment
        ), f'length="" must never be int()-cast into size_in_bytes, got {attachment!r}'


class TestDates:
    """Spec: date_published/date_modified are "RFC 3339 format"; we accept datetime.fromisoformat as the check."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_dates_parse_as_iso8601_when_present(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            for field in ("date_published", "date_modified"):
                if field not in item:
                    continue
                value = item[field]
                assert isinstance(
                    value, str
                ), f"{source}/{kind}/{feed_dir.name} item[{i}].{field}={value!r} is not a string"
                try:
                    datetime.fromisoformat(value)
                except ValueError as exc:
                    pytest.fail(f"{source}/{kind}/{feed_dir.name} item[{i}].{field}={value!r} is not ISO 8601: {exc}")

    def test_rdf_dc_date_from_model_extra_is_still_emitted(self):
        """RDF has no core <pubDate> - dc:date lives in model_extra and must not be lost."""
        feed_dir = next(d for s, k, d in FEEDS if k == "rdf" and d.name == "slashdot")
        feed, doc, _ = _load("corpus", "rdf", feed_dir)

        source_items = get_source_items(feed)
        assert source_items, "tests/corpus/rdf/slashdot has no items - fixture changed?"
        assert all("dc:date" in (item.content.model_extra or {}) for item in source_items), (
            "tests/corpus/rdf/slashdot/data.xml no longer carries dc:date in model_extra - "
            "this test's premise needs updating"
        )

        for i, item in enumerate(doc["items"]):
            assert "date_published" in item or "date_modified" in item, (
                f"corpus/rdf/slashdot item[{i}] (id={item.get('id')!r}): dc:date from model_extra "
                "was not surfaced as date_published/date_modified"
            )


class TestNoNullFields:
    """The contract: omit a field rather than emit it as null. The spec never sanctions null values either -
    every field it defines is typed as string/array/boolean/number, never nullable.
    """

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_no_null_anywhere_in_the_document(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        nulls = list(find_nulls(doc))
        assert not nulls, f"{source}/{kind}/{feed_dir.name}: null value(s) at {nulls}"


class TestExtensionNaming:
    """Spec: extension field "names must start with an _ character". 4.4.0 emits none, so this suite
    just makes sure nothing non-spec ever sneaks in unprefixed.
    """

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_feed_level_extensions_are_prefixed(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for key in doc:
            if key not in FEED_LEVEL_SPEC_FIELDS:
                assert key.startswith("_"), (
                    f"{source}/{kind}/{feed_dir.name}: non-spec feed field {key!r} is not an "
                    "underscore-prefixed extension"
                )

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_item_level_extensions_are_prefixed(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        for i, item in enumerate(doc.get("items", [])):
            for key in item:
                if key not in ITEM_LEVEL_SPEC_FIELDS:
                    assert key.startswith("_"), (
                        f"{source}/{kind}/{feed_dir.name} item[{i}]: non-spec item field {key!r} is not "
                        "an underscore-prefixed extension"
                    )


class TestJsonRoundTrip:
    """The whole point of the format: it must be exactly reproducible JSON, nothing exotic."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_dumps_loads_round_trips_unchanged(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        serialized = json.dumps(doc, allow_nan=False)
        assert json.loads(serialized) == doc, f"{source}/{kind}/{feed_dir.name}: round-trip mismatch"

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_no_non_json_types_anywhere(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        offenders = list(find_non_json_types(doc))
        assert not offenders, f"{source}/{kind}/{feed_dir.name}: {offenders}"


class TestFeedUrlParameter:
    """feed_url is "unknowable from the document" per the contract - it must be opt-in only."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_feed_url_absent_without_the_kwarg(self, source, kind, feed_dir):
        _, doc, _ = _load(source, kind, feed_dir)

        assert "feed_url" not in doc, f"{source}/{kind}/{feed_dir.name}: feed_url present without feed_url="

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_feed_url_present_when_passed(self, source, kind, feed_dir):
        feed, _, _ = _load(source, kind, feed_dir)
        url = f"https://example.com/{kind}/{feed_dir.name}/feed.json"

        doc, _ = to_json_feed(feed, feed_url=url)

        assert doc.get("feed_url") == url, f"{source}/{kind}/{feed_dir.name}: feed_url={doc.get('feed_url')!r}"


class TestReportConsistency:
    """The JsonFeedReport counts must be independently reproducible from the output, not just self-reported."""

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_report_type_and_nonnegative_counts(self, source, kind, feed_dir):
        _, _, report = _load(source, kind, feed_dir)

        assert isinstance(report, JsonFeedReport), f"{source}/{kind}/{feed_dir.name}: {type(report)!r}"
        assert report.dropped_items >= 0, f"{source}/{kind}/{feed_dir.name}: dropped_items={report.dropped_items}"
        assert (
            report.dropped_attachments >= 0
        ), f"{source}/{kind}/{feed_dir.name}: dropped_attachments={report.dropped_attachments}"
        assert report.unparsed_dates >= 0, f"{source}/{kind}/{feed_dir.name}: unparsed_dates={report.unparsed_dates}"

    @pytest.mark.parametrize(("source", "kind", "feed_dir"), FEEDS, ids=FEED_IDS)
    def test_dropped_items_equals_source_minus_emitted(self, source, kind, feed_dir):
        feed, doc, report = _load(source, kind, feed_dir)

        source_count = len(get_source_items(feed))
        emitted_count = len(doc.get("items", []))

        assert report.dropped_items == source_count - emitted_count, (
            f"{source}/{kind}/{feed_dir.name}: report.dropped_items={report.dropped_items}, but source had "
            f"{source_count} items and {emitted_count} were emitted (expected "
            f"dropped_items={source_count - emitted_count})"
        )
