from typing import List, Optional


from pydantic import BaseModel


class DescriptionImage(BaseModel):
    alt: Optional[str]
    source: str


class FeedItem(BaseModel):
    title: str
    link: str
    description: str
    language: str  # en-us
    copyright: Optional[str]  # Copyright 2002, Spartanburg Herald-Journal
    pub_date: Optional[str]
    category: Optional[str]
    description_links: Optional[List[str]]
    description_images: Optional[List[DescriptionImage]]
    other: Optional[dict]

    # stackoverflow.com/questions/10994229/how-to-make-an-object-properly-hashable
    # added this, so you can call/use FeedItems in a set() to avoid duplicates
    def __hash__(self):
        return hash(self.title.strip())

    def __eq__(self, other):
        return self.title.strip() == other.title.strip()


class RSSFeed(BaseModel):
    title: str
    version: Optional[str]
    language: Optional[str]
    description: Optional[str]
    feed: List[FeedItem]
