from typing import Optional

from bs4 import BeautifulSoup

from .models import RSSFeed

import re

class Parser:
    def __init__(self, xml: str, limit=None):
        self.xml = xml
        self.limit = limit

        self.raw_data = None
        self.rss = None

    @staticmethod
    def get_soup(xml: str, parser: str = "xml") -> BeautifulSoup:
        return BeautifulSoup(xml, parser)

    @staticmethod
    def check_none(
            item: object,
            default: str,
            item_dict: Optional[str] = None,
            default_dict: Optional[str] = None,
    ):
        if item:
            return item[item_dict]
        else:
            if default_dict:
                return default[default_dict]
            else:
                return default

    def parse(self, entries: []) -> RSSFeed:
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
            description_soup = self.get_soup(getattr(getattr(item, "description"), "text", ""), "html.parser")

            item_dict = {
                "title": getattr(getattr(item, "title", ""), "text", ""),
                "link": getattr(getattr(item, "link", ""), "text", ""),
                "publish_date": getattr(getattr(item, "pubDate", ""), "text", ""),
                "category": getattr(getattr(item, "category", ""), "text", ""),
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
                    value = getattr(getattr(item, entrie, ""), "text", "")
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
