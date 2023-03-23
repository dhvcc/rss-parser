import re
from typing import Any, List, Optional

from xmltodict import parse

from rss_parser.models.root import Channel, RSSFeed


class Parser:
    """Parser for rss files."""

    def __init__(self, xml: str, limit=None, *, root_model=RSSFeed):
        self.xml = xml
        self.limit = limit

        self.raw_data = None
        self.rss = None

        self.root_model = root_model

    @staticmethod
    def _check_atom(root: dict):
        if "feed" in root:
            raise NotImplementedError("ATOM feed is not currently supported")  #

    # @staticmethod
    # def check_none(
    #         item: object,
    #         default: str,
    #         item_dict: Optional[str] = None,
    #         default_dict: Optional[str] = None,
    # ) -> Any:
    #     """
    #     Check if the item_dict in item.py is None, else returns default_dict of default.
    #
    #     :param item: The first object.
    #     :param default: The default object.
    #     :param item_dict: The item.py dictionary.
    #     :param default_dict: The default dictionary.
    #     :return: The (not None) final object.
    #     """
    #     if item:
    #         return item[item_dict]
    #     else:
    #         if default_dict:
    #             return default[default_dict]
    #         else:
    #             return default
    #
    # @staticmethod
    # def get_text(item: object, attribute: str) -> str:
    #     """
    #     Return the text information about an attribute of an object.
    #
    #     If it is not present, it will return an empty string.
    #     :param item: The object with the attribute
    #     :param attribute: The attribute which has a 'text' attribute
    #     :return: The string of the text of the specified attribute
    #     """
    #     return getattr(getattr(item, attribute, ""), "text", "")
    #
    def parse(self) -> RSSFeed:
        """
        Parse the rss and each item.py of the feed.

        Missing attributes will be replaced by an empty string. The
        information of the optional entries are stored in a dictionary
        under the attribute "other" of each item.py.

        :param entries: An optional list of additional rss tags that can be recovered
        from each item.py
        :return: The RSSFeed which describe the rss information
        """
        root = parse(self.xml)
        self._check_atom(root)

        m = self.root_model.parse_obj(root["rss"])

        return m
