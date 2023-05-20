"""
Models created according to https://www.rssboard.org/rss-specification.

Some types and validation may be a bit custom to account for broken standards in some RSS feeds.
"""
from typing import Type

from pydantic import BaseModel, create_model
from typing_extensions import Self

from rss_parser.models.types.tag import Tag
from rss_parser.models.utils import camel_case, extract_tag_sub_type


class RSSBaseModel(BaseModel):
    class Config:
        # Not really sure if we want for the schema obj to be immutable
        # Disabling for now
        # allow_mutation = False
        alias_generator = camel_case

    @classmethod
    def _extend_model_tags(cls, with_: bool, fields: list):
        attrs = {}
        for key, value in cls.__fields__.items():
            if "__all__" in fields or key in fields:
                if with_:
                    transform = lambda t: t if issubclass(t, Tag) else Tag[t]  # noqa
                else:
                    transform = lambda t: extract_tag_sub_type(t) if issubclass(t, Tag) else t  # noqa
                attrs[key] = (transform(value.type_), value.default)
            else:
                attrs[key] = (value.type_, value.default)
        return create_model(f"{cls.__name__}__extended", __base__=RSSBaseModel, **attrs)

    @classmethod
    def without_tags(cls, *fields) -> Type[Self]:
        return cls._extend_model_tags(with_=False, fields=fields)

    @classmethod
    def with_tags(cls, *fields) -> Type[Self]:
        return cls._extend_model_tags(with_=True, fields=fields)
