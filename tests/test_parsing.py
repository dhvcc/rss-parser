from json import dumps

import pytest

from rss_parser import Parser


@pytest.mark.parametrize("sample_and_result", [["rss_2"], ["rss_2_no_category_attr"], ["apology_line"]], indirect=True)
def test_parses_rss_version_2(sample_and_result):
    # Expect basic RSSv2 to be parsed
    sample, result = sample_and_result
    parser = Parser(xml=sample)
    rss = parser.parse()

    assert rss

    left = rss.json(indent=2, sort_keys=True)
    right = dumps(result, indent=2, sort_keys=True, default=str)

    assert left == right


@pytest.mark.parametrize(
    "sample_and_result", [["rss_2", True], ["rss_2_no_category_attr", True], ["apology_line", True]], indirect=True
)
def test_json_plain_ignores_attributes(sample_and_result):
    # Expect basic RSSv2 to be parsed
    sample, result = sample_and_result
    parser = Parser(xml=sample)
    rss = parser.parse()

    assert rss

    left = rss.json_plain(indent=2, sort_keys=True)
    right = dumps(result, indent=2, sort_keys=True, default=str)

    assert left == right


def test_fails_atom_feed(atom_feed):
    # Expect ATOM feed to fail since it's not supported
    parser = Parser(xml=atom_feed)

    with pytest.raises(NotImplementedError):
        parser.parse()
