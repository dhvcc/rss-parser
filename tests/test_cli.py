"""
CLI tests.

``main(argv)`` is called in-process - a subprocess per case would cost 15 CI legs more
than it proves.
"""

import json
from unittest.mock import Mock

import pytest

from rss_parser.cli import EXIT_OK, EXIT_REJECTED, EXIT_SIGPIPE, EXIT_USAGE, main
from tests.conftest import iter_corpus, iter_samples

FEEDS = [str(feed_dir / "data.xml") for _, feed_dir in (*iter_samples(), *iter_corpus())]
FEED_IDS = [f"{kind}/{feed_dir.name}" for kind, feed_dir in (*iter_samples(), *iter_corpus())]

RSS_2 = (
    '<rss version="2.0"><channel><title>T</title><link>L</link><description>D</description>'
    "<item><title>One</title></item></channel></rss>"
)
ATOM = (
    '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:x</id><title>T</title>'
    "<entry><id>urn:1</id><title>E</title></entry></feed>"
)
ENTITIES = (
    '<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
    '<rss version="2.0"><channel><title>&xxe;</title><link>L</link><description>D</description></channel></rss>'
)


SELF_CLOSING_CHANNEL = '<rss version="2.0"><channel/></rss>'


def write_feed(tmp_path, data: str, name: str = "feed.xml") -> str:
    path = tmp_path / name
    path.write_text(data, encoding="utf-8")
    return str(path)


class TestExitCodes:
    """The docs publish these numbers as a contract, so pin the literals, not the constants."""

    def test_the_documented_values(self):
        assert (EXIT_OK, EXIT_REJECTED, EXIT_USAGE, EXIT_SIGPIPE) == (0, 1, 2, 141)

    def test_success_really_returns_zero(self, tmp_path):
        assert main(["validate", write_feed(tmp_path, RSS_2)]) == 0

    def test_a_rejected_feed_really_returns_one(self, tmp_path, capsys):
        assert main(["validate", write_feed(tmp_path, "<html/>")]) == 1
        capsys.readouterr()

    def test_a_usage_error_really_returns_two(self, capsys):
        assert main(["validate", "https://example.com/feed.xml"]) == 2
        capsys.readouterr()

    def test_a_closed_stdout_really_returns_141(self, tmp_path, monkeypatch):
        monkeypatch.setattr("rss_parser.cli._detach_stdout", lambda: None)
        monkeypatch.setattr("sys.stdout", None)  # what Python does when fd 1 is closed (`>&-`)

        assert main(["parse", write_feed(tmp_path, RSS_2)]) == 141

    def test_validate_still_succeeds_with_a_closed_stdout(self, tmp_path, monkeypatch):
        """`rss-parser validate feed.xml >&-` must not crash on sys.stdout being None."""
        monkeypatch.setattr("sys.stdout", None)

        assert main(["validate", write_feed(tmp_path, RSS_2)]) == 0


class TestValidate:
    @pytest.mark.parametrize("feed", FEEDS, ids=FEED_IDS)
    def test_every_feed_in_the_tree_validates(self, feed, capsys):
        assert main(["validate", feed]) == EXIT_OK

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    @pytest.mark.parametrize("feed", FEEDS, ids=FEED_IDS)
    def test_json_report_is_valid_for_every_feed(self, feed, capsys):
        assert main(["validate", "--json", feed]) == EXIT_OK

        report = json.loads(capsys.readouterr().out)
        assert report["valid"] is True
        assert report["feed_type"] in {"rss", "atom", "rdf"}
        assert report["items"] >= 0

    def test_stdin_is_the_default_input(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", FakeStdin(RSS_2.encode()))

        assert main(["validate"]) == EXIT_OK

    def test_explicit_dash_reads_stdin(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", FakeStdin(ATOM.encode()))

        assert main(["validate", "-"]) == EXIT_OK


class FakeStdin:
    def __init__(self, data: bytes):
        self.buffer = _Buffer(data)


class _Buffer:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


FAILURE_CASES = [
    ("", "invalid_xml", "not well-formed"),
    ("not xml at all", "invalid_xml", "not well-formed"),
    ("<rss><channel>unclosed", "invalid_xml", "not well-formed"),
    ("<rss></feed>", "invalid_xml", "not well-formed"),
    ("<html><body>hi</body></html>", "unknown_feed_type", "Could not detect the feed type"),
    (ENTITIES, "entities_disabled", "entities are disabled"),
    (
        "<rss><channel><title>T</title><description>D</description></channel></rss>",
        "schema_violation",
        "validation error",
    ),
    (
        '<rss version="2.0"><channel><title>T</title><link>L</link><description>D</description>'
        "<item><author>a@example.com</author></item></channel></rss>",
        "schema_violation",
        "validation error",
    ),
    (
        '<feed xmlns="http://www.w3.org/2005/Atom"><title>No id here</title></feed>',
        "schema_violation",
        "validation error",
    ),
]
FAILURE_IDS = [
    "empty",
    "plain-text",
    "unclosed-tag",
    "mismatched-tag",
    "html-root",
    "dtd-entities",
    "channel-without-link",
    "item-without-title-or-description",
    "atom-without-id",
]


class TestValidateFailures:
    @pytest.mark.parametrize(("data", "message"), [(c[0], c[2]) for c in FAILURE_CASES], ids=FAILURE_IDS)
    def test_human_output_goes_to_stderr(self, data, message, tmp_path, capsys):
        assert main(["validate", write_feed(tmp_path, data)]) == EXIT_REJECTED

        captured = capsys.readouterr()
        assert captured.out == ""
        assert message in captured.err
        assert captured.err.startswith("rss-parser: ")

    @pytest.mark.parametrize(("data", "code"), [(c[0], c[1]) for c in FAILURE_CASES], ids=FAILURE_IDS)
    def test_json_report_carries_the_code(self, data, code, tmp_path, capsys):
        assert main(["validate", "--json", write_feed(tmp_path, data)]) == EXIT_REJECTED

        report = json.loads(capsys.readouterr().out)
        assert report["valid"] is False
        assert report["error"]["code"] == code

    def test_binary_junk_is_rejected(self, tmp_path, capsys):
        path = tmp_path / "feed.xml"
        path.write_bytes(b"\x00\x01\x02")

        assert main(["validate", str(path)]) == EXIT_REJECTED
        assert "not well-formed" in capsys.readouterr().err

    def test_schema_violation_details_point_at_the_element(self, tmp_path, capsys):
        data = "<rss><channel><title>T</title><description>D</description></channel></rss>"

        main(["validate", "--json", write_feed(tmp_path, data)])

        (detail,) = json.loads(capsys.readouterr().out)["error"]["details"]
        assert detail == {"loc": "channel.content.link", "type": "missing", "msg": "Field required"}

    def test_wrong_parser_for_the_feed_type_is_a_schema_violation(self, tmp_path, capsys):
        assert main(["validate", "--parser", "atom", write_feed(tmp_path, RSS_2)]) == EXIT_REJECTED
        assert "validation error" in capsys.readouterr().err

    def test_an_unrecognized_value_error_is_not_labelled_a_feed_verdict(self, tmp_path, monkeypatch, capsys):
        """Anything that is not one of the four library errors is our bug, not the feed's fault."""
        monkeypatch.setattr("rss_parser.cli._parse", Mock(side_effect=ValueError("something odd")))

        assert main(["validate", "--json", write_feed(tmp_path, RSS_2)]) == EXIT_REJECTED

        error = json.loads(capsys.readouterr().out)["error"]
        assert error["code"] == "internal_error"
        assert "unexpected ValueError: something odd" == error["message"]

    def test_json_writes_nothing_on_a_usage_error(self, capsys):
        assert main(["validate", "--json", "https://example.com/feed.xml"]) == EXIT_USAGE

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "does not fetch feeds" in captured.err

    def test_an_empty_channel_is_valid_and_reports_no_items(self, tmp_path, capsys):
        """A documented non-goal: Tag.content is Optional, so <channel/> satisfies the schema."""
        assert main(["validate", "--json", write_feed(tmp_path, SELF_CLOSING_CHANNEL)]) == EXIT_OK

        report = json.loads(capsys.readouterr().out)
        assert report == {"valid": True, "feed_type": "rss", "items": 0}

    def test_feed_type_is_reported_even_when_the_schema_fails(self, tmp_path, capsys):
        data = "<rss><channel><title>T</title><description>D</description></channel></rss>"

        main(["validate", "--json", write_feed(tmp_path, data)])

        assert json.loads(capsys.readouterr().out)["feed_type"] == "rss"


class TestValidateStrict:
    BAD_DATE = (
        '<rss version="2.0"><channel><title>T</title><link>L</link><description>D</description>'
        "<item><title>One</title><pubDate>whenever</pubDate></item></channel></rss>"
    )

    def test_unparsed_date_is_accepted_without_strict(self, tmp_path):
        assert main(["validate", write_feed(tmp_path, self.BAD_DATE)]) == EXIT_OK

    def test_strict_rejects_it_and_names_the_path(self, tmp_path, capsys):
        assert main(["validate", "--strict", write_feed(tmp_path, self.BAD_DATE)]) == EXIT_REJECTED

        err = capsys.readouterr().err
        assert "1 date(s) could not be parsed" in err
        assert "channel.items[0].pub_date: whenever" in err

    def test_strict_json_report(self, tmp_path, capsys):
        assert main(["validate", "--strict", "--json", write_feed(tmp_path, self.BAD_DATE)]) == EXIT_REJECTED

        report = json.loads(capsys.readouterr().out)
        assert report["error"]["code"] == "unparsed_dates"
        assert report["error"]["details"] == [{"loc": "channel.items[0].pub_date", "value": "whenever"}]

    def test_strict_passes_on_parseable_dates(self, tmp_path):
        data = self.BAD_DATE.replace("whenever", "Sat, 07 Sep 2002 00:00:01 GMT")

        assert main(["validate", "--strict", write_feed(tmp_path, data)]) == EXIT_OK

    @pytest.mark.parametrize("feed", FEEDS, ids=FEED_IDS)
    def test_no_feed_in_the_tree_has_an_unparsable_date(self, feed, capsys):
        assert main(["validate", "--strict", feed]) == EXIT_OK, capsys.readouterr().err


class TestParse:
    def test_dumps_the_typed_model(self, tmp_path, capsys):
        assert main(["parse", write_feed(tmp_path, RSS_2)]) == EXIT_OK

        payload = json.loads(capsys.readouterr().out)
        assert payload["channel"]["content"]["title"] == {"content": "T", "attributes": {}}

    def test_indent_pretty_prints(self, tmp_path, capsys):
        main(["parse", "--indent", "2", write_feed(tmp_path, RSS_2)])

        out = capsys.readouterr().out
        assert out.startswith("{\n  ")
        assert json.loads(out)

    def test_flat_emits_null_for_attribute_only_tags(self, tmp_path, capsys):
        """The documented --flat wart: dict_plain() flattens a Tag to its content, which is None."""
        data = RSS_2.replace("<item><title>One</title>", '<item><title>One</title><enclosure url="u" length="1"/>')

        main(["parse", "--flat", write_feed(tmp_path, data)])

        payload = json.loads(capsys.readouterr().out)
        assert payload["channel"]["title"] == "T"
        assert payload["channel"]["items"][0]["enclosures"] == [None]

    def test_ascii_escapes_non_ascii(self, tmp_path, capsys):
        data = RSS_2.replace("<title>T</title>", "<title>Привет</title>", 1)

        main(["parse", "--ascii", write_feed(tmp_path, data)])

        assert "\\u041f" in capsys.readouterr().out

    def test_utf8_is_kept_by_default(self, tmp_path, capsys):
        data = RSS_2.replace("<title>T</title>", "<title>Привет</title>", 1)

        main(["parse", write_feed(tmp_path, data)])

        assert "Привет" in capsys.readouterr().out

    def test_indent_is_not_accepted_by_items(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["items", "--indent", "2", write_feed(tmp_path, RSS_2)])

        assert exc_info.value.code == EXIT_USAGE

    def test_a_rejected_feed_exits_1(self, tmp_path, capsys):
        assert main(["parse", write_feed(tmp_path, "<html/>")]) == EXIT_REJECTED

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Could not detect the feed type" in captured.err


class TestItems:
    @pytest.mark.parametrize("feed", FEEDS, ids=FEED_IDS)
    def test_one_json_object_per_item(self, feed, capsys):
        assert main(["items", feed]) == EXIT_OK
        out = capsys.readouterr().out

        assert out.endswith("\n")
        lines = out.splitlines()
        for line in lines:
            assert json.loads(line)

        capsys.readouterr()
        main(["validate", "--json", feed])
        assert len(lines) == json.loads(capsys.readouterr().out)["items"]

    def test_records_never_contain_a_literal_newline(self, tmp_path, capsys):
        data = RSS_2.replace("<title>One</title>", "<title>line one\nline two</title>")

        main(["items", write_feed(tmp_path, data)])
        out = capsys.readouterr().out

        assert len(out.splitlines()) == 1
        assert "line one\\nline two" in out

    def test_attributes_are_kept(self, tmp_path, capsys):
        data = RSS_2.replace("<item>", '<item><guid isPermaLink="false">g</guid>')

        main(["items", write_feed(tmp_path, data)])

        record = json.loads(capsys.readouterr().out)
        assert record["content"]["guid"]["attributes"] == {"is_perma_link": "false"}

    def test_ascii_escapes_non_ascii(self, tmp_path, capsys):
        data = RSS_2.replace("<title>One</title>", "<title>Привет</title>")

        main(["items", "--ascii", write_feed(tmp_path, data)])

        assert "\\u041f" in capsys.readouterr().out

    def test_atom_entries_are_the_items(self, tmp_path, capsys):
        main(["items", write_feed(tmp_path, ATOM)])

        record = json.loads(capsys.readouterr().out)
        assert record["content"]["id"]["content"] == "urn:1"

    def test_an_empty_feed_emits_nothing_and_succeeds(self, tmp_path, capsys):
        """A self-closing <channel/> is an empty feed, not an unknown schema."""
        assert main(["items", write_feed(tmp_path, SELF_CLOSING_CHANNEL)]) == EXIT_OK

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_an_empty_atom_feed_emits_nothing_and_succeeds(self, tmp_path, capsys):
        assert main(["items", write_feed(tmp_path, '<feed xmlns="http://www.w3.org/2005/Atom"/>')]) == EXIT_OK
        assert capsys.readouterr().out == ""


class TestItemsFlat:
    def test_flat_drops_the_wrapping_tag_and_flattens_the_content(self, tmp_path, capsys):
        main(["items", "--flat", write_feed(tmp_path, RSS_2)])

        record = json.loads(capsys.readouterr().out)
        assert record["title"] == "One"
        assert "content" not in record

    def test_flat_emits_null_for_attribute_only_tags(self, tmp_path, capsys):
        data = RSS_2.replace("<item><title>One</title>", '<item><title>One</title><enclosure url="u" length="1"/>')

        main(["items", "--flat", write_feed(tmp_path, data)])

        assert json.loads(capsys.readouterr().out)["enclosures"] == [None]

    def test_flat_is_still_one_record_per_line(self, tmp_path, capsys):
        data = RSS_2.replace("</channel>", "<item><title>Two</title></item></channel>")

        main(["items", "--flat", write_feed(tmp_path, data)])

        lines = capsys.readouterr().out.splitlines()
        assert [json.loads(line)["title"] for line in lines] == ["One", "Two"]

    def test_a_self_closing_item_has_no_content_to_flatten(self, tmp_path, capsys):
        data = RSS_2.replace("<item>", "<item/><item>")

        main(["items", "--flat", write_feed(tmp_path, data)])

        first, second = (json.loads(line) for line in capsys.readouterr().out.splitlines())
        assert (first, second["title"]) == ({}, "One")


class TestInputErrors:
    def test_a_url_gets_the_pipe_hint(self, capsys):
        assert main(["validate", "https://example.com/feed.xml"]) == EXIT_USAGE

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "does not fetch feeds" in captured.err
        assert "curl -sSL https://example.com/feed.xml | rss-parser validate -" in captured.err

    def test_the_hint_names_the_verb_that_was_used(self, capsys):
        assert main(["items", "http://example.com/feed.xml"]) == EXIT_USAGE
        assert "| rss-parser items -" in capsys.readouterr().err

    def test_a_missing_file_exits_2(self, tmp_path, capsys):
        assert main(["validate", str(tmp_path / "nope.xml")]) == EXIT_USAGE
        assert "No such file or directory" in capsys.readouterr().err

    def test_a_directory_exits_2(self, tmp_path, capsys):
        assert main(["validate", str(tmp_path)]) == EXIT_USAGE
        assert "is a directory" in capsys.readouterr().err

    def test_an_unknown_flag_shows_the_subcommands_usage(self, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["parse", "--json", write_feed(tmp_path, RSS_2)])

        assert exc_info.value.code == EXIT_USAGE
        err = capsys.readouterr().err
        assert err.startswith("usage: rss-parser parse")
        assert "unrecognized arguments: --json" in err

    def test_an_unknown_verb_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["detect", "feed.xml"])

        assert exc_info.value.code == EXIT_USAGE

    def test_no_verb_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            main([])

        assert exc_info.value.code == EXIT_USAGE


class TestParserSelection:
    PODCAST = (
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel>'
        "<title>T</title><link>L</link><description>D</description>"
        "<itunes:author>Ann</itunes:author><item><title>One</title></item></channel></rss>"
    )

    def test_podcast_parser_types_itunes_fields(self, tmp_path, capsys):
        assert main(["parse", "--parser", "podcast", write_feed(tmp_path, self.PODCAST)]) == EXIT_OK

        channel = json.loads(capsys.readouterr().out)["channel"]["content"]
        assert channel["itunes_author"] == {"content": "Ann", "attributes": {}}

    def test_auto_keeps_itunes_fields_untyped(self, tmp_path, capsys):
        assert main(["parse", write_feed(tmp_path, self.PODCAST)]) == EXIT_OK

        channel = json.loads(capsys.readouterr().out)["channel"]["content"]
        assert "itunes_author" not in channel
        assert channel["itunes:author"] == "Ann"

    @pytest.mark.parametrize("name", ["rss", "atom", "rdf", "podcast"])
    def test_every_parser_is_selectable(self, name, tmp_path):
        data = {"rss": RSS_2, "podcast": self.PODCAST, "atom": ATOM}.get(name)
        if data is None:  # rdf needs a real RDF document
            data = (
                '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                "<channel><title>T</title><link>L</link><description>D</description></channel>"
                "<item><title>One</title><link>L</link></item></rdf:RDF>"
            )

        assert main(["validate", "--parser", name, write_feed(tmp_path, data)]) == EXIT_OK


class TestCustomSchema:
    MODULE = """
from pydantic import Field
from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss import RSS
from rss_parser.models.rss.channel import Channel
from rss_parser.models.rss.item import Item
from rss_parser.models.types.tag import Tag


class MyItem(Item):
    creator: Optional[Tag[str]] = Field(alias="dc:creator", default=None)


MySchema = RSS[Channel[MyItem]]
NotASchema = 42
"""
    FEED = RSS_2.replace("<title>One</title>", '<title>One</title><dc:creator xmlns:dc="d">Ann</dc:creator>')

    @pytest.fixture
    def module_dir(self, tmp_path, monkeypatch):
        (tmp_path / "my_schema.py").write_text(self.MODULE, encoding="utf-8")
        monkeypatch.chdir(tmp_path)  # the CLI appends os.getcwd() to sys.path itself
        return tmp_path

    def test_custom_schema_is_used(self, module_dir, capsys):
        assert main(["parse", "--schema", "my_schema:MySchema", write_feed(module_dir, self.FEED)]) == EXIT_OK

        item = json.loads(capsys.readouterr().out)["channel"]["content"]["items"][0]["content"]
        assert item["creator"]["content"] == "Ann"

    def test_custom_schema_validates(self, module_dir):
        assert main(["validate", "--schema", "my_schema:MySchema", write_feed(module_dir, self.FEED)]) == EXIT_OK

    def test_a_malformed_spec_exits_2(self, capsys):
        assert main(["validate", "--schema", "my_schema", "feed.xml"]) == EXIT_USAGE
        assert "must look like module.path:ClassName" in capsys.readouterr().err

    def test_an_unimportable_module_exits_2(self, capsys):
        assert main(["validate", "--schema", "no_such_module:X", "feed.xml"]) == EXIT_USAGE
        assert "is not importable" in capsys.readouterr().err

    @pytest.mark.usefixtures("module_dir")
    def test_a_missing_attribute_exits_2(self, capsys):
        assert main(["validate", "--schema", "my_schema:Nope", "feed.xml"]) == EXIT_USAGE
        assert "has no attribute 'Nope'" in capsys.readouterr().err

    @pytest.mark.usefixtures("module_dir")
    def test_a_non_model_attribute_exits_2(self, capsys):
        assert main(["validate", "--schema", "my_schema:NotASchema", "feed.xml"]) == EXIT_USAGE
        assert "is not an XMLBaseModel subclass" in capsys.readouterr().err

    def test_schema_and_parser_are_mutually_exclusive(self, capsys):
        assert main(["validate", "--parser", "rss", "--schema", "my_schema:MySchema", "feed.xml"]) == EXIT_USAGE
        assert "mutually exclusive" in capsys.readouterr().err

    def test_items_cannot_guess_a_custom_root_schema(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "flat_schema.py").write_text(
            "from rss_parser.models import XMLBaseModel\n"
            "from rss_parser.models.types.tag import Tag\n\n\n"
            "class Flat(XMLBaseModel):\n"
            "    channel: Tag[dict]\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        assert main(["items", "--schema", "flat_schema:Flat", write_feed(tmp_path, RSS_2)]) == EXIT_USAGE
        assert "cannot locate the items of a custom --schema" in capsys.readouterr().err

    def test_validate_omits_the_item_count_for_a_custom_root_schema(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "flat2_schema.py").write_text(
            "from rss_parser.models import XMLBaseModel\n"
            "from rss_parser.models.types.tag import Tag\n\n\n"
            "class Flat(XMLBaseModel):\n"
            "    channel: Tag[dict]\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        assert main(["validate", "--json", "--schema", "flat2_schema:Flat", write_feed(tmp_path, RSS_2)]) == EXIT_OK

        report = json.loads(capsys.readouterr().out)
        assert report["valid"] is True
        assert "items" not in report


class TestBrokenPipe:
    def test_a_closed_stdout_exits_141(self, tmp_path, monkeypatch):
        """
        `rss-parser items feed.xml | head -1` must not traceback.

        The devnull redirect itself is stubbed out: dup2 onto the real stdout fd would take
        pytest's own capture with it, which is why _detach_stdout is a separate, pragma'd function.
        """

        def explode(_text):
            raise BrokenPipeError

        monkeypatch.setattr("sys.stdout.write", explode)
        monkeypatch.setattr("rss_parser.cli._detach_stdout", lambda: None)

        assert main(["items", write_feed(tmp_path, RSS_2)]) == EXIT_SIGPIPE


JSONFEED_RSS = RSS_2.replace("<item><title>One</title></item>", "<item><title>One</title><guid>g</guid></item>")

DROPPED_ITEM_RSS = (
    '<rss version="2.0"><channel><title>T</title><link>http://example.com</link><description>D</description>'
    "<item><description>No title, no guid, no link</description></item>"
    "<item><guid>g</guid><title>Kept</title></item></channel></rss>"
)


class TestJsonFeed:
    def test_dumps_a_json_feed_document(self, tmp_path, capsys):
        assert main(["jsonfeed", write_feed(tmp_path, JSONFEED_RSS)]) == EXIT_OK

        document = json.loads(capsys.readouterr().out)
        assert document["version"] == "https://jsonfeed.org/version/1.1"
        assert document["items"][0]["title"] == "One"

    def test_indent_pretty_prints(self, tmp_path, capsys):
        main(["jsonfeed", "--indent", "2", write_feed(tmp_path, JSONFEED_RSS)])

        out = capsys.readouterr().out
        assert out.startswith("{\n  ")
        assert json.loads(out)

    def test_ascii_escapes_non_ascii(self, tmp_path, capsys):
        data = JSONFEED_RSS.replace("<title>T</title>", "<title>Привет</title>", 1)

        main(["jsonfeed", "--ascii", write_feed(tmp_path, data)])

        assert "\\u041f" in capsys.readouterr().out

    def test_feed_url_is_omitted_by_default(self, tmp_path, capsys):
        main(["jsonfeed", write_feed(tmp_path, JSONFEED_RSS)])

        assert "feed_url" not in json.loads(capsys.readouterr().out)

    def test_feed_url_flag_sets_it(self, tmp_path, capsys):
        main(["jsonfeed", "--feed-url", "https://example.com/f.xml", write_feed(tmp_path, JSONFEED_RSS)])

        assert json.loads(capsys.readouterr().out)["feed_url"] == "https://example.com/f.xml"

    def test_a_dropped_item_is_reported_on_stderr_and_exit_is_still_zero(self, tmp_path, capsys):
        exit_code = main(["jsonfeed", write_feed(tmp_path, DROPPED_ITEM_RSS)])

        captured = capsys.readouterr()
        assert exit_code == EXIT_OK
        assert len(json.loads(captured.out)["items"]) == 1
        assert captured.err == "rss-parser: dropped 1 item without an id\n"

    def test_dropped_attachments_and_unparsed_dates_are_both_reported(self, tmp_path, capsys):
        data = JSONFEED_RSS.replace(
            "<guid>g</guid>",
            '<guid>g</guid><enclosure url="http://x/a.mp3"/><pubDate>not a date</pubDate>',
        )

        exit_code = main(["jsonfeed", write_feed(tmp_path, data)])

        captured = capsys.readouterr()
        assert exit_code == EXIT_OK
        assert captured.err == (
            "rss-parser: dropped 1 attachment without a url or mime type, omitted 1 unparseable date\n"
        )

    def test_a_rejected_feed_exits_1(self, tmp_path, capsys):
        assert main(["jsonfeed", write_feed(tmp_path, "<html/>")]) == EXIT_REJECTED

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_a_custom_schema_root_is_a_usage_error(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "flat_schema.py").write_text(
            "from rss_parser.models import XMLBaseModel\n"
            "from rss_parser.models.types.tag import Tag\n\n\n"
            "class Flat(XMLBaseModel):\n"
            "    channel: Tag[dict]\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main(["jsonfeed", "--schema", "flat_schema:Flat", write_feed(tmp_path, JSONFEED_RSS)])

        assert exit_code == EXIT_USAGE
        assert "cannot map a custom --schema to JSON Feed" in capsys.readouterr().err


class TestItemsJsonFeed:
    def test_emits_json_feed_item_objects(self, tmp_path, capsys):
        assert main(["items", "--jsonfeed", write_feed(tmp_path, JSONFEED_RSS)]) == EXIT_OK

        record = json.loads(capsys.readouterr().out)
        assert record["title"] == "One"
        assert record["content_text"] == ""

    def test_atom_entries_too(self, tmp_path, capsys):
        main(["items", "--jsonfeed", write_feed(tmp_path, ATOM)])

        record = json.loads(capsys.readouterr().out)
        assert record["id"] == "urn:1"

    def test_a_dropped_item_is_reported_on_stderr(self, tmp_path, capsys):
        exit_code = main(["items", "--jsonfeed", write_feed(tmp_path, DROPPED_ITEM_RSS)])

        captured = capsys.readouterr()
        assert exit_code == EXIT_OK
        assert len(captured.out.splitlines()) == 1
        assert captured.err == "rss-parser: dropped 1 item without an id\n"

    def test_flat_and_jsonfeed_are_mutually_exclusive(self, tmp_path, capsys):
        exit_code = main(["items", "--flat", "--jsonfeed", write_feed(tmp_path, RSS_2)])

        assert exit_code == EXIT_USAGE
        assert "--flat and --jsonfeed are mutually exclusive" in capsys.readouterr().err
