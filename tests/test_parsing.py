import pytest

from rss_parser import Parser


def test_parses_rss_version_2(rss_version_2, rss_version_2_data_dict):
    # Expect basic RSSv2 to be parsed
    parser = Parser(xml=rss_version_2)
    rss = parser.parse()

    assert rss
    assert rss.dict() == rss_version_2_data_dict


def test_fails_atom_feed(atom_feed):
    # Expect ATOM feed to fail since it's not supported
    parser = Parser(xml=atom_feed)

    with pytest.raises(NotImplementedError):
        parser.parse()
