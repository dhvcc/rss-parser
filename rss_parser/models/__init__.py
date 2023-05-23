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
        # Not really sure if we want for the schema obj to be immutable, disabling for now
        # allow_mutation = False
        alias_generator = camel_case

    @classmethod
    def _extend_model_tags(cls, wrap: bool, fields: list):
        """Oprionally wraps/unwraps Tag type for specified fields, supports __all__."""
        attrs = {}
        for key, value in cls.__fields__.items():
            if "__all__" in fields or key in fields:
                if wrap:
                    transform = lambda t: t if Tag.is_tag(t) else Tag[t]  # noqa
                else:
                    transform = lambda t: extract_tag_sub_type(t) if Tag.is_tag(t) else t  # noqa
                attrs[key] = (transform(value.type_), value.default)
            else:
                attrs[key] = (value.type_, value.default)
        return create_model(cls.__name__, __base__=RSSBaseModel, **attrs)

    @classmethod
    def unwrap_tags(cls, *fields: str) -> Type[Self]:
        """
        Unwraps povided fields with Tag[field].

        Providing __all__ will apply this to everey model field.
        """
        return cls._extend_model_tags(wrap=False, fields=fields)

    @classmethod
    def wrap_tags(cls, *fields: str) -> Type[Self]:
        """
        Wraps povided fields with Tag[field] if they're not already.

        Providing __all__ will apply this to everey model field.
        """
        return cls._extend_model_tags(wrap=True, fields=fields)
