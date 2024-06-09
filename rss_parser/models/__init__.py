"""
Models created according to https://www.rssboard.org/rss-specification.

Some types and validation may be a bit custom to account for broken standards in some RSS feeds.
"""
from json import loads

from rss_parser.models.utils import camel_case
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class XMLBaseModel(pydantic.BaseModel):
    class Config:
        alias_generator = camel_case

    def json_plain(self, **kw):
        """
        Run pydantic's json with custom encoder to encode Tags as only content.
        """
        from rss_parser.models.types.tag import Tag

        return self.json(models_as_dict=False, encoder=Tag.flatten_tag_encoder, **kw)

    def dict_plain(self, **kw):
        return loads(self.json_plain(**kw))
