import re
from typing import Any, List, Optional

from bs4 import BeautifulSoup

from .models import RSSFeed


class Parser:
    """Parser for rss files."""

    def __init__(self, xml: str, limit=None):
        self.xml = xml
        self.limit = limit

        self.raw_data = None
        self.rss = None

    @staticmethod
    def _check_atom(soup: BeautifulSoup):
        if soup.feed:
            raise NotImplementedError("ATOM feed is not currently supported")

    @classmethod
    def get_soup(cls, xml: str, parser: str = "xml") -> BeautifulSoup:
        """
        Get the BeautifulSoup object with a specified parser.

        :param xml: The xml content
        :param parser: The parser type. Default is xml
        :return: The BeautifulSoup object
        """
        soup = BeautifulSoup(xml, parser)
        cls._check_atom(soup)
        return soup

    @staticmethod
    def check_none(
        item: object,
        default: str,
        item_dict: Optional[str] = None,
        default_dict: Optional[str] = None,
    ) -> Any:
        """
        Check if the item_dict in item is None, else returns default_dict of default.

        :param item: The first object.
        :param default: The default object.
        :param item_dict: The item dictionary.
        :param default_dict: The default dictionary.
        :return: The (not None) final object.
        """
        if item:
            return item[item_dict]
        else:
            if default_dict:
                return default[default_dict]
            else:
                return default

    @staticmethod
    def get_text(item: object, attribute: str) -> str:
        """
        Return the text information about an attribute of an object.

        If it is not present, it will return an empty string.
        :param item: The object with the attribute
        :param attribute: The attribute which has a 'text' attribute
        :return: The string of the text of the specified attribute
        """
        return getattr(getattr(item, attribute, ""), "text", "")

    def parse(self, entries: Optional[List[str]] = List) -> RSSFeed:
        """
        Parse the rss and each item of the feed.

        Missing attributes will be replaced by an empty string. The
        information of the optional entries are stored in a dictionary
        under the attribute "other" of each item.

        :param entries: An optional list of additional rss tags that can be recovered
        from each item
        :return: The RSSFeed which describe the rss information
        """
        main_soup = self.get_soup(self.xml)

        self.raw_data = {
            "title": main_soup.title.text,
            "version": main_soup.rss.get("version"),
            "language": getattr(main_soup.language, "text", ""),
            "description": getattr(main_soup.description, "text", ""),
            "feed": [],
        }

        items = main_soup.findAll("item")

        if self.limit is not None:
            items = items[: self.limit]

        for item in items:
            # Using html.parser instead of lxml because lxml can't parse <link>
            description_soup = self.get_soup(
                self.get_text(item, "description"), "html.parser"
            )

            item_dict = {
                "title": self.get_text(item, "title"),
                "link": self.get_text(item, "link"),
                "publish_date": self.get_text(item, "pubDate"),
                "category": self.get_text(item, "category"),
                "description": getattr(description_soup, "text", ""),
                "description_links": [
                    anchor.get("href")
                    for anchor in description_soup.findAll("a")
                    # if statement to avoid non true values in the list
                    if anchor.get("href")
                ],
                "description_images": [
                    {"alt": image.get("alt", ""), "source": image.get("src")}
                    for image in description_soup.findAll("img")
                ],
            }

            try:
                # Add user-defined entries
                item_dict.update({"other": {}})
                for entrie in entries:
                    value = self.get_text(item, entrie)
                    value = re.sub(f"</?{entrie}>", "", value)
                    item_dict["other"].update({entrie: value})

                item_dict.update(
                    {
                        "enclosure": {
                            "content": "",
                            "attrs": {
                                "url": item.enclosure["url"],
                                "length": item.enclosure["length"],
                                "type": item.enclosure["type"],
                            },
                        },
                        "itunes": {
                            "content": "",
                            "attrs": {
                                "href": self.check_none(
                                    item.find("itunes:image"),
                                    main_soup.find("itunes:image"),
                                    "href",
                                    "href",
                                )
                            },
                        },
                    }
                )
            except (TypeError, KeyError, AttributeError):
                pass

            self.raw_data["feed"].append(item_dict)

        return RSSFeed(**self.raw_data)
