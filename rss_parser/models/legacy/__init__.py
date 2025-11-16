"""
Models created according to https://www.rssboard.org/rss-specification.

Some types and validation may be a bit custom to account for broken standards in some RSS feeds.
"""

from json import loads
from typing import TYPE_CHECKING

from rss_parser.models.legacy.pydantic_proxy import import_v1_pydantic
from rss_parser.models.legacy.utils import camel_case

if TYPE_CHECKING:
    from pydantic import v1 as pydantic
else:
    pydantic = import_v1_pydantic()


class XMLBaseModel(pydantic.BaseModel):
    class Config:
        alias_generator = camel_case

    def json_plain(self, **kw):
        """
        Run pydantic's json with custom encoder to encode Tags as only content.
        """
        from rss_parser.models.legacy.types.tag import Tag  # noqa: PLC0415

        return self.json(models_as_dict=False, encoder=Tag.flatten_tag_encoder, **kw)

    def dict_plain(self, **kw):
        return loads(self.json_plain(**kw))
