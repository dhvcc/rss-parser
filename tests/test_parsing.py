from json import dumps

import pytest

from rss_parser import Parser


@pytest.mark.parametrize(
    "sample_and_result",
    [
        # ["rss_2"], ["rss_2_no_category_attr"], ["apology_line"],
        ["rss_2_with_1_item"]
    ],
    indirect=True,
)
def test_parses_all_samples(sample_and_result):
    sample, result = sample_and_result
    rss = Parser.parse(sample)

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
    rss = Parser.parse(sample)

    assert rss

    left = rss.json_plain(indent=2, sort_keys=True)
    right = dumps(result, indent=2, sort_keys=True, default=str)

    assert left == right


def test_fails_atom_feed(atom_feed):
    # Expect ATOM feed to fail since it's not supported
    with pytest.raises(NotImplementedError):
        Parser.parse(atom_feed)
