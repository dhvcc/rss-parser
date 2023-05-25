from xmltodict import parse

from rss_parser.models.root import RSS

# >>> FUTURE
# TODO: May be support generator based approach for big rss feeds
# TODO: Add cli to parse to json
# TODO: Possibly bundle as deb/rpm/exe
# TODO: Atom support
# TODO: Older RSS versions?

# >>>> MVP
# TODO: Parser class based approach, use classmethods and class attributes
# TODO: Also add dynamic class generator with config.
# Parser.with_config which returns new class and also supports context managers
class Parser:
    """Parser for rss files."""

    def __init__(self, xml: str, limit=None, *, schema=RSS):
        self.xml = xml
        self.limit = limit

        self.raw_data = None
        self.rss = None

        self.schema = schema

    @staticmethod
    def _check_atom(root: dict):
        if "feed" in root:
            raise NotImplementedError("ATOM feed is not currently supported")

    def parse(self) -> RSS:
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
