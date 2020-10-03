from typing import List, Optional

from pydantic import BaseModel


class DescriptionImage(BaseModel):
    alt: Optional[str]
    source: str


class FeedItem(BaseModel):
    title: str
    link: str
    publish_date: Optional[str]
    category: Optional[str]
    description: str
    description_links: Optional[List[str]]
    description_images: Optional[List[DescriptionImage]]


class RSSFeed(BaseModel):
    title: str
    version: Optional[str]
    language: Optional[str]
    description: Optional[str]
    feed: List[FeedItem]
