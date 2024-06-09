import logging
from typing import Type

import pytest

from rss_parser import AtomParser, BaseParser, RSSParser

logger = logging.getLogger(__name__)


class DataHelper:
    @staticmethod
    def compare_parsing(sample_and_result, parser: Type[BaseParser]):
        sample, result = sample_and_result
        rss = parser.parse(sample)

        assert rss

        parsed = rss.dict()
        assert parsed == result


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
    def test_parses_all_rss_samples(self, sample_and_result):
        DataHelper.compare_parsing(sample_and_result, parser=RSSParser)


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
    def test_parses_all_atom_samples(self, sample_and_result):
        DataHelper.compare_parsing(sample_and_result, parser=AtomParser)
