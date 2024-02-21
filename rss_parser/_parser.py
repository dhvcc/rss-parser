from typing import ClassVar, Optional, Type

from xmltodict import parse

from rss_parser.custom_decorators import abstract_class_attributes
from rss_parser.models import XMLBaseModel
from rss_parser.models.atom import Atom
from rss_parser.models.rss import RSS

# >>> FUTURE
# TODO: May be support generator based approach for big rss feeds
# TODO: Add cli to parse to json
# TODO: Possibly bundle as deb/rpm/exe
# TODO: Older Atom versions
# TODO: Older RSS versions


@abstract_class_attributes("schema")
class BaseParser:
    """Parser for rss/atom files."""

    schema: ClassVar[Type[XMLBaseModel]]
    root_key: Optional[str] = None

    @staticmethod
    def to_xml(data: str, *args, **kwargs):
        return parse(str(data), *args, **kwargs)

    @classmethod
    def parse(
        cls,
        data: str,
        *,
        schema: Optional[Type[XMLBaseModel]] = None,
        root_key: Optional[str] = None,
    ) -> XMLBaseModel:
        """
        Parse XML data into schema.
        :param data: string of XML data that needs to be parsed
        :return: "schema" object
        """
        root = cls.to_xml(data)

        schema = schema if schema else cls.schema

        root_key = root_key if root_key else cls.root_key

        if root_key:
            root = root.get(root_key, root)

        return schema.parse_obj(root)


class AtomParser(BaseParser):
    schema = Atom


class RSSParser(BaseParser):
    root_key = "rss"
    schema = RSS
