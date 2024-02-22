from json import dumps

import pytest

from rss_parser import AtomParser, RSSParser


@pytest.mark.parametrize(
    "sample_and_result",
    [
        ["rss_2"],
        ["rss_2_no_category_attr"],
        ["apology_line"],
        ["rss_2_with_1_item"],
    ],
    indirect=True,
)
def test_parses_all_rss_samples(sample_and_result):
    sample, result = sample_and_result
    rss = RSSParser.parse(sample)

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
    rss = RSSParser.parse(sample)

    assert rss

    left = rss.json_plain(indent=2, sort_keys=True)
    right = dumps(result, indent=2, sort_keys=True, default=str)

    assert left == right


@pytest.mark.parametrize(
    "sample_and_result",
    [
        ["atom"],
        ["generic_atom_feed"],
    ],
    indirect=True,
)
def test_parses_all_atom_samples(sample_and_result):
    sample, result = sample_and_result
    atom = AtomParser.parse(sample)

    assert atom

    left = atom.json(indent=2, sort_keys=True)
    right = dumps(result, indent=2, sort_keys=True, default=str)

    assert left == right


@pytest.mark.parametrize(
    "sample_and_result",
    [
        ["atom", True],
        ["generic_atom_feed", True],
    ],
    indirect=True,
)
def test_json_plain_ignores_attributes_atom(sample_and_result):
    # Expect basic RSSv2 to be parsed
    sample, result = sample_and_result
    rss = AtomParser.parse(sample)

    assert rss

    left = rss.json_plain(indent=2, sort_keys=True)
    right = dumps(result, indent=2, sort_keys=True, default=str)

    assert left == right
