from xmltodict import parse

from rss_parser.models.root import RSSFeed


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
