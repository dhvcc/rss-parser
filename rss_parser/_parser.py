from typing import Optional, Type

from xmltodict import parse

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom import Atom
from rss_parser.models.rss import RSS

# >>> FUTURE
# TODO: May be support generator based approach for big rss feeds
# TODO: Add cli to parse to json
# TODO: Possibly bundle as deb/rpm/exe
# TODO: Older Atom versions
# TODO: Older RSS versions


class Parser:
    """Parser for rss files."""

    @staticmethod
    def check_schema(root: dict) -> tuple[dict, type[XMLBaseModel]]:
        if "feed" in root:
            return root, Atom
        return root["rss"], RSS

    @staticmethod
    def to_xml(data: str, *args, **kwargs):
        return parse(str(data), *args, **kwargs)

    @classmethod
    def parse(cls, data: str, *, schema: Optional[Type[XMLBaseModel]] = None, root_key: str = "") -> XMLBaseModel:
        """
        Parse XML data into schema (default: RSS 2.0).

        :param data: string of XML data that needs to be parsed
        :return: "schema" object
        """
        root = cls.to_xml(data)
        if not isinstance(schema, XMLBaseModel):
            root, schema = cls.check_schema(root)
        else:
            root = root.get(root_key, root)

        return schema.parse_obj(root)
