from typing import Type

import pytest

from rss_parser import AtomParser, BaseParser, RSSParser
from rss_parser.models.legacy.atom import Atom as LegacyAtom
from rss_parser.models.legacy.rss import RSS as LegacyRSS


class LegacyRSSParser(RSSParser):
    schema = LegacyRSS


class LegacyAtomParser(AtomParser):
    schema = LegacyAtom


class DataHelper:
    @staticmethod
    def compare_parsing(sample_and_result, parser: Type[BaseParser]):
        sample, result = sample_and_result
        rss = parser.parse(sample)

        assert rss

        if hasattr(rss, "model_dump"):
            parsed = rss.model_dump()
        else:
            parsed = rss.dict()
        assert parsed == result


RSS_PARSERS = pytest.mark.parametrize(
    "parser_cls",
    [RSSParser, LegacyRSSParser],
    ids=["rss-v2", "rss-legacy"],
)

ATOM_PARSERS = pytest.mark.parametrize(
    "parser_cls",
    [AtomParser, LegacyAtomParser],
    ids=["atom-v2", "atom-legacy"],
)


@pytest.mark.usefixtures("sample_and_result")
class TestRSS:
    @pytest.mark.parametrize(
        "sample_and_result",
        [
            ["rss_2"],
            ["rss_2_no_category_attr"],
            ["apology_line"],
            ["rss_2_with_1_item"],
            ["github-49"],
        ],
        indirect=True,
    )
    @RSS_PARSERS
    def test_parses_all_rss_samples(self, sample_and_result, parser_cls):
        DataHelper.compare_parsing(sample_and_result, parser=parser_cls)


@pytest.mark.usefixtures("sample_and_result")
class TestAtom:
    @pytest.mark.parametrize(
        "sample_and_result",
        [
            ["atom"],
            ["generic_atom_feed"],
        ],
        indirect=True,
    )
    @ATOM_PARSERS
    def test_parses_all_atom_samples(self, sample_and_result, parser_cls):
        DataHelper.compare_parsing(sample_and_result, parser=parser_cls)
