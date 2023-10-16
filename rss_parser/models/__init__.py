"""
Models created according to https://www.rssboard.org/rss-specification.

Some types and validation may be a bit custom to account for broken standards in some RSS feeds.
"""
from json import loads

from pydantic import BaseModel
from pydantic.json import pydantic_encoder

from rss_parser.models.utils import camel_case


class XMLBaseModel(BaseModel):
    class Config:
        # Not really sure if we want for the schema obj to be immutable, disabling for now
        # allow_mutation = False
        arbitrary_types_allowed = True

        alias_generator = camel_case

    def json_plain(self, **kw):
        """
        Run pydantic's json with custom encoder to encode Tags as only content.
        """
        from rss_parser.models.types import Tag

        return self.json(models_as_dict=False, encoder=Tag.flatten_tag_encoder, **kw)

    def dict_plain(self, **kw):
        return loads(self.json_plain(**kw))
