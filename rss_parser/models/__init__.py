"""
Models created according to https://www.rssboard.org/rss-specification.

Some types and validation may be a bit custom to account for broken standards in some RSS feeds.
"""
from pydantic import BaseModel


class RSSBaseModel(BaseModel):
    # TODO: Override func to be abel to input camel

    class Config:
        allow_mutation = False
