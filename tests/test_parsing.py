import sys
from typing import Type

import pytest

from rss_parser import AtomParser, BaseParser, RSSParser

if sys.version_info < (3, 14):
    from rss_parser.models.legacy.atom import Atom as LegacyAtom
    from rss_parser.models.legacy.rss import RSS as LegacyRSS

    class LegacyRSSParser(RSSParser):
        schema = LegacyRSS

    class LegacyAtomParser(AtomParser):
        schema = LegacyAtom

    rss_parser_list = [RSSParser, LegacyRSSParser]
    rss_ids = ["rss-v2", "rss-legacy"]
    atom_parser_list = [AtomParser, LegacyAtomParser]
    atom_ids = ["atom-v2", "atom-legacy"]
else:
    rss_parser_list = [RSSParser]
    rss_ids = ["rss-v2"]
    atom_parser_list = [AtomParser]
    atom_ids = ["atom-v2"]


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
    rss_parser_list,
    ids=rss_ids,
)

ATOM_PARSERS = pytest.mark.parametrize(
    "parser_cls",
    atom_parser_list,
    ids=atom_ids,
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


class TestLegacyImportError:
    @pytest.mark.skipif(sys.version_info < (3, 14), reason="Legacy models still work in Python 3.13 and below")
    def test_legacy_import_error(self):
        with pytest.raises(ImportError):
            from rss_parser.models.legacy import XMLBaseModel  # noqa: F401, PLC0415
