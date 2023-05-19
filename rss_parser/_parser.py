from xmltodict import parse

from rss_parser.models.root import RSSFeed

# >>> FUTURE
# TODO: Feature, ignore_attributes in to_dict to allow for clean output
# TODO: May be support generator based approach for big rss feeds
# TODO: Add cli to parse to json
# TODO: Possibly bundle as deb/rpm/exe

# >>>> MVP
# FIXME: doesn't parse items on https://rss.art19.com/apology-line
# Related. Provide a way to auto populate nested models. May be a custom class, like TagList or a custom validator
#
# TODO: Arithmetic operators
# TODO: class based approach, use classmethods and class attributes
# TODO: Also add dynamic class generator with config.
# Parser.with_config which returns new class and also supports context managers
# TODO: Limit, xml, schema can be set in config or in runtime
class Parser:
    """Parser for rss files."""

    def __init__(self, xml: str, limit=None, *, schema=RSSFeed):
        self.xml = xml
        self.limit = limit

        self.raw_data = None
        self.rss = None

        self.schema = schema

    @staticmethod
    def _check_atom(root: dict):
        if "feed" in root:
            raise NotImplementedError("ATOM feed is not currently supported")  #

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

        return self.schema.parse_obj(root["rss"])
