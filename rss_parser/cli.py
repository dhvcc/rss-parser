"""
Command line interface for rss-parser: ``validate``, ``parse``, ``items`` and ``jsonfeed``.

Nothing here fetches anything - feeds arrive on stdin or as a local file, which keeps the
library's no-networking promise intact. See ``rss-parser --help`` or docs/cli.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterator, Sequence
from importlib import import_module
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rss_parser._parser import (
    DEFAULT_PARSERS,
    AtomParser,
    BaseParser,
    EntitiesDisabledError,
    InvalidXMLError,
    PodcastParser,
    RDFParser,
    RSSParser,
    UnknownFeedTypeError,
    detect_feed_type,
)
from rss_parser._parser import parse as parse_feed
from rss_parser.jsonfeed import JsonFeedReport, to_json_feed
from rss_parser.models import XMLBaseModel
from rss_parser.models.atom import Atom
from rss_parser.models.rdf import RDF
from rss_parser.models.rss import RSS
from rss_parser.models.types.date import DateTimeOrStr
from rss_parser.models.types.tag import Tag

EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_USAGE = 2
EXIT_SIGPIPE = 141  # 128 + SIGPIPE, so `set -o pipefail` can tell `| head` from a bad feed

PARSERS: dict[str, type[BaseParser]] = {
    "rss": RSSParser,
    "atom": AtomParser,
    "rdf": RDFParser,
    "podcast": PodcastParser,
}

VALIDATE_NON_GOALS = """
validate checks well-formedness, the root element, and the elements the models require.
It is not a spec conformance checker: an unparsable <pubDate>, a misspelled tag, a <link>
that is not a URL or a channel with no items all pass. Use --strict for the dates.
"""

JSONFEED_NOTES = """
Lossy on purpose: an item with no derivable id is dropped, because the spec requires one and
this never synthesizes it. There is no itunes:* mapping - use `parse --parser podcast` for
that. Atom xhtml content cannot be safely re-serialized (xmltodict reorders mixed content), so
it falls back to <summary> and finally to an empty content_text.
"""


class UsageError(Exception):
    """Anything that makes the invocation itself unusable - always exit 2."""


def _read_input(source: str, command: str) -> bytes:
    """Read the feed as bytes, so the document's own encoding declaration decides decoding."""
    if source == "-":
        return sys.stdin.buffer.read()
    if source.startswith(("http://", "https://")):
        raise UsageError(f"does not fetch feeds. Pipe it instead:\n    curl -sSL {source} | rss-parser {command} -")
    path = Path(source)
    if path.is_dir():  # Windows raises PermissionError here, so don't rely on the OSError type
        raise UsageError(f"{source}: is a directory")
    try:
        return path.read_bytes()
    except OSError as e:
        raise UsageError(f"{source}: {e.strerror}") from e


def _load_schema(spec: str) -> type[XMLBaseModel]:
    """Import a custom ``XMLBaseModel`` subclass from a ``module.path:ClassName`` spec."""
    module_name, separator, attribute = spec.partition(":")
    if not (module_name and separator and attribute):
        raise UsageError(f"--schema must look like module.path:ClassName, got {spec!r}")
    # Appended, never inserted: a local json.py must not shadow the standard library
    sys.path.append(os.getcwd())
    try:
        module = import_module(module_name)
    except ImportError as e:
        raise UsageError(f"--schema module {module_name!r} is not importable: {e}") from e
    try:
        schema = getattr(module, attribute)
    except AttributeError:
        raise UsageError(f"--schema {spec!r}: {module_name!r} has no attribute {attribute!r}") from None
    if not (isinstance(schema, type) and issubclass(schema, XMLBaseModel)):
        raise UsageError(f"--schema {spec!r} is not an XMLBaseModel subclass")
    return schema


def _parse(data: bytes, parser_name: str, schema: type[XMLBaseModel] | None) -> XMLBaseModel:
    if parser_name == "auto":
        if schema is None:
            return parse_feed(data)
        parser = DEFAULT_PARSERS[detect_feed_type(data)]
    else:
        parser = PARSERS[parser_name]
    return parser.parse(data, schema=schema)


def _feed_items(feed: XMLBaseModel) -> list[Tag] | None:
    """
    The items of a known feed model, or None for a custom --schema we know nothing about.

    A self-closing <channel/> or <feed/> has no content and therefore no items - that is an empty
    feed, not an unknown schema, so it must not be reported as a --schema problem.
    """
    if isinstance(feed, RSS):
        return [] if feed.channel.content is None else feed.channel.content.items
    if isinstance(feed, Atom):
        return [] if feed.feed.content is None else feed.feed.content.entries
    if isinstance(feed, RDF):
        return feed.items
    return None


def _classify(exc: ValueError) -> tuple[str, str, list[dict[str, Any]]]:
    """Map a library error onto a --json ``error.code``, a message and its details."""
    if isinstance(exc, ValidationError):  # most specific first - it is a ValueError too
        details = [
            {"loc": ".".join(str(part) for part in error["loc"]), "type": error["type"], "msg": error["msg"]}
            for error in exc.errors()
        ]
        return "schema_violation", str(exc).splitlines()[0], details
    if isinstance(exc, EntitiesDisabledError):
        return "entities_disabled", f"{exc}: DTD entities are refused before expansion", []
    if isinstance(exc, InvalidXMLError):
        return "invalid_xml", str(exc), []
    if isinstance(exc, UnknownFeedTypeError):
        return "unknown_feed_type", str(exc).splitlines()[0], []
    # Any other ValueError is a bug here or upstream, not a verdict about the feed
    return "internal_error", f"unexpected {type(exc).__name__}: {exc}", []


def _is_date_tag(tag: Tag) -> bool:
    """True for a Tag[DateTimeOrStr]: each parametrization carries its own content annotation."""
    return DateTimeOrStr in getattr(type(tag).model_fields["content"].annotation, "__args__", ())


def _iter_tags(value: Any, path: str) -> Iterator[tuple[str, Tag]]:
    if isinstance(value, Tag):
        yield path, value
        yield from _iter_tags(value.content, path)
    elif isinstance(value, XMLBaseModel):
        for name in type(value).model_fields:
            yield from _iter_tags(getattr(value, name), f"{path}.{name}" if path else name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_tags(item, f"{path}[{index}]")


def _unparsed_dates(feed: XMLBaseModel) -> list[dict[str, Any]]:
    """Every date field whose value stayed a string because it parsed as neither RFC 822 nor ISO 8601."""
    return [
        {"loc": path, "value": tag.content}
        for path, tag in _iter_tags(feed, "")
        if isinstance(tag.content, str) and _is_date_tag(tag)
    ]


def _validate(data: bytes, args: argparse.Namespace, schema: type[XMLBaseModel] | None) -> int:
    report: dict[str, Any] = {"valid": False, "feed_type": None}
    try:
        report["feed_type"] = detect_feed_type(data).value
        feed = _parse(data, args.parser, schema)
    except ValueError as exc:
        code, message, details = _classify(exc)
        report["error"] = {"code": code, "message": message, "details": details}
        return _report(report, args.json, message, details)

    items = _feed_items(feed)
    if items is not None:
        report["items"] = len(items)

    unparsed = _unparsed_dates(feed) if args.strict else []
    if unparsed:
        message = f"{len(unparsed)} date(s) could not be parsed"
        report["error"] = {"code": "unparsed_dates", "message": message, "details": unparsed}
        return _report(report, args.json, message, [{"loc": d["loc"], "msg": d["value"]} for d in unparsed])

    report["valid"] = True
    if args.json:
        _write(json.dumps(report, ensure_ascii=False) + "\n")
    return EXIT_OK


def _report(report: dict[str, Any], as_json: bool, message: str, details: Sequence[dict[str, Any]]) -> int:
    """Write a rejection either as a JSON report on stdout or as human text on stderr."""
    if as_json:
        _write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        lines = [f"rss-parser: {message}"] + [f"  {detail['loc']}: {detail['msg']}" for detail in details]
        sys.stderr.write("\n".join(lines) + "\n")
    return EXIT_REJECTED


def _write(text: str) -> None:
    if sys.stdout is None:
        # fd 1 was already closed (`>&-`, or pythonw.exe) - the same situation as a closed pipe
        raise BrokenPipeError("stdout is closed")
    sys.stdout.write(text)
    sys.stdout.flush()  # so `| head -3` truncates immediately instead of buffering


def _dump(feed: XMLBaseModel, args: argparse.Namespace) -> int:
    payload = feed.dict_plain() if args.flat else feed.model_dump(mode="json")
    _write(json.dumps(payload, indent=args.indent, ensure_ascii=args.ascii) + "\n")
    return EXIT_OK


def _to_json_feed(feed: XMLBaseModel, feed_url: str | None = None) -> tuple[dict[str, Any], JsonFeedReport]:
    try:
        return to_json_feed(feed, feed_url=feed_url)
    except TypeError as exc:
        raise UsageError("cannot map a custom --schema to JSON Feed; use `rss-parser parse` instead") from exc


def _jsonfeed_summary(report: JsonFeedReport) -> str | None:
    """The stderr line for whatever ``to_json_feed`` dropped or omitted - never silent (decision 2)."""

    def _plural(count: int, noun: str) -> str:
        return f"{count} {noun}{'' if count == 1 else 's'}"

    parts = []
    if report.dropped_items:
        parts.append(f"dropped {_plural(report.dropped_items, 'item')} without an id")
    if report.dropped_attachments:
        parts.append(f"dropped {_plural(report.dropped_attachments, 'attachment')} without a url or mime type")
    if report.unparsed_dates:
        parts.append(f"omitted {_plural(report.unparsed_dates, 'unparseable date')}")
    return f"rss-parser: {', '.join(parts)}" if parts else None


def _write_jsonfeed_summary(report: JsonFeedReport) -> None:
    message = _jsonfeed_summary(report)
    if message is not None:
        sys.stderr.write(message + "\n")


def _jsonfeed(feed: XMLBaseModel, args: argparse.Namespace) -> int:
    document, report = _to_json_feed(feed, args.feed_url)
    _write(json.dumps(document, indent=args.indent, ensure_ascii=args.ascii) + "\n")
    _write_jsonfeed_summary(report)
    return EXIT_OK


def _items(feed: XMLBaseModel, args: argparse.Namespace) -> int:
    if args.jsonfeed:
        if args.flat:
            raise UsageError("--flat and --jsonfeed are mutually exclusive")
        document, report = _to_json_feed(feed)
        for record in document["items"]:
            _write(json.dumps(record, ensure_ascii=args.ascii) + "\n")
        _write_jsonfeed_summary(report)
        return EXIT_OK

    items = _feed_items(feed)
    if items is None:
        raise UsageError("cannot locate the items of a custom --schema; use `rss-parser parse` instead")
    for item in items:
        if not args.flat:
            record = item.model_dump(mode="json")
        else:  # a self-closing <item/> has no content at all
            record = {} if item.content is None else item.content.dict_plain()
        _write(json.dumps(record, ensure_ascii=args.ascii) + "\n")
    return EXIT_OK


def _run(args: argparse.Namespace) -> int:
    if args.schema and args.parser != "auto":
        raise UsageError("--schema and --parser are mutually exclusive (--schema replaces the schema)")
    schema = _load_schema(args.schema) if args.schema else None
    data = _read_input(args.file, args.command)

    if args.command == "validate":
        return _validate(data, args, schema)

    try:
        feed = _parse(data, args.parser, schema)
    except ValueError as exc:
        _, message, details = _classify(exc)
        lines = [f"rss-parser: {message}"] + [f"  {detail['loc']}: {detail['msg']}" for detail in details]
        sys.stderr.write("\n".join(lines) + "\n")
        return EXIT_REJECTED

    if args.command == "parse":
        return _dump(feed, args)
    if args.command == "jsonfeed":
        return _jsonfeed(feed, args)
    return _items(feed, args)


def _build_parser() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """Build the parser plus a map of the subparsers, so errors can show the right usage."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("file", nargs="?", default="-", help="feed file, or - for stdin (the default)")
    common.add_argument(
        "--parser",
        choices=["auto", *PARSERS],
        default="auto",
        help="auto detects from the root element; podcast is the only way to get typed itunes:* fields, "
        "because auto maps <rss> to the plain RSS schema",
    )
    common.add_argument(
        "--schema",
        metavar="module.path:ClassName",
        help="replace the schema with a custom XMLBaseModel subclass. Executes that module's code; "
        "the current directory is added to sys.path so a local module works",
    )

    parser = argparse.ArgumentParser(
        prog="rss-parser",
        description="Validate and convert RSS 2.0/0.9x, Atom 1.0 and RSS 1.0 (RDF) feeds. Never fetches: "
        "pipe with curl or pass a file.",
        epilog="Exit codes: 0 ok, 1 feed rejected, 2 usage error, 141 stdout closed early.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", parents=[common], help="check a feed against the schema", description=VALIDATE_NON_GOALS.strip()
    )
    validate.add_argument("--json", action="store_true", help="write a machine-readable report to stdout")
    validate.add_argument(
        "--strict", action="store_true", help="also reject dates that parsed as neither RFC 822 nor ISO 8601"
    )

    dump = subparsers.add_parser("parse", parents=[common], help="dump the validated model as JSON")
    dump.add_argument(
        "--flat",
        action="store_true",
        help="flatten every tag to its content (dict_plain). Lossy: attribute-only tags such as "
        "<enclosure> and Atom <link> have no content and come out as null",
    )
    dump.add_argument("--indent", type=int, metavar="N", help="pretty-print with N spaces")
    dump.add_argument("--ascii", action="store_true", help="escape non-ASCII characters")

    items = subparsers.add_parser("items", parents=[common], help="one JSON object per item (NDJSON)")
    items.add_argument(
        "--flat",
        action="store_true",
        help="emit the item itself with every tag flattened to its content, so `jq -r '.title'` works "
        "instead of `.content.title.content`. Lossy: the wrapping tag's attributes are dropped and "
        "attribute-only tags such as <enclosure> come out as null",
    )
    items.add_argument(
        "--jsonfeed",
        action="store_true",
        help="emit JSON Feed 1.1 item objects instead, using the same mapper as `jsonfeed`. Mutually "
        "exclusive with --flat. See `rss-parser jsonfeed --help` for what is lossy",
    )
    items.add_argument("--ascii", action="store_true", help="escape non-ASCII characters")

    jsonfeed = subparsers.add_parser(
        "jsonfeed",
        parents=[common],
        help="dump the feed as a JSON Feed 1.1 document",
        description=JSONFEED_NOTES.strip(),
    )
    jsonfeed.add_argument("--indent", type=int, metavar="N", help="pretty-print with N spaces")
    jsonfeed.add_argument("--ascii", action="store_true", help="escape non-ASCII characters")
    jsonfeed.add_argument(
        "--feed-url",
        metavar="URL",
        help="set the feed_url field. Unknowable from the document itself, so omitted unless given here",
    )

    return parser, {"validate": validate, "parse": dump, "items": items, "jsonfeed": jsonfeed}


def _detach_stdout() -> None:  # pragma: no cover - would clobber the test runner's own stdout
    """Point stdout at devnull so the interpreter's shutdown flush does not fail a second time."""
    if sys.stdout is not None:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``rss-parser`` console script. Returns the process exit code."""
    # On Windows a piped stdout defaults to the ANSI code page, which raises on non-ASCII feed
    # text; the explicit newline keeps NDJSON records \n-terminated everywhere. sys.stdout is None
    # when fd 1 is closed (`>&-`) or under pythonw.exe, and not every stream is reconfigurable
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", newline="\n")

    parser, verbs = _build_parser()
    args, extras = parser.parse_known_args(argv)
    if extras:
        # argparse reports leftovers on the top-level parser, whose usage is not the one the user needs
        verbs[args.command].error(f"unrecognized arguments: {' '.join(extras)}")
    try:
        return _run(args)
    except UsageError as exc:
        sys.stderr.write(f"rss-parser: {exc}\n")
        return EXIT_USAGE
    except BrokenPipeError:
        _detach_stdout()
        return EXIT_SIGPIPE
