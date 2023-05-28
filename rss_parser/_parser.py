from typing import ClassVar, Optional, Type

from xmltodict import parse

from rss_parser.models import XMLBaseModel
from rss_parser.models.rss import RSS

# >>> FUTURE
# TODO: May be support generator based approach for big rss feeds
# TODO: Add cli to parse to json
# TODO: Possibly bundle as deb/rpm/exe
# TODO: Atom support
# TODO: Older RSS versions?


class Parser:
    """Parser for rss files."""

    schema: ClassVar[Type[XMLBaseModel]] = RSS

    @staticmethod
    def _check_atom(root: dict):
        if "feed" in root:
            raise NotImplementedError("ATOM feed is not currently supported")

    @staticmethod
    def to_xml(data: str, *args, **kwargs):
        return parse(str(data), *args, **kwargs)

    @classmethod
    def parse(cls, data: str, *, schema: Optional[Type[XMLBaseModel]] = None) -> XMLBaseModel:
        """
        Parse XML data into schema (default: RSS 2.0).

        :param data: string of XML data that needs to be parsed
        :return: "schema" object
        """
        root = cls.to_xml(data)
        cls._check_atom(root)

        schema = schema or cls.schema

        return schema.parse_obj(root["rss"])
