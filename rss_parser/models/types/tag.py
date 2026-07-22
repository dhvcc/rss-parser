from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Generic, Optional, TypeVar, Union

from pydantic import BaseModel, Field, model_validator
from pydantic.json import pydantic_encoder

from rss_parser.models import XMLBaseModel
from rss_parser.models.utils import snake_case

T = TypeVar("T")


class Tag(BaseModel, Generic[T]):
    """
    Generic wrapper around a single XML tag, splitting its text into ``content``
    and its XML attributes into ``attributes``.

    >>> from rss_parser.models import XMLBaseModel
    >>> from rss_parser.models.types.tag import Tag
    >>> class Model(XMLBaseModel):
    ...     width: Tag[int]
    ...     category: Tag[str]
    >>> m = Model(
    ...     width=48,
    ...     category={"@someAttribute": "https://example.com", "#text": "valid string"},
    ... )
    >>> # Content value is an integer, as per the generic type
    >>> m.width.content
    48
    >>> # Tags stringify to their content, so print() shows what you expect
    >>> str(m.width)
    '48'
    >>> # The attributes are empty by default
    >>> m.width.attributes
    {}
    >>> # But are populated when provided.
    >>> # Note that the @ symbol is trimmed from the beginning and the name is converted to snake_case
    >>> m.category.attributes
    {'some_attribute': 'https://example.com'}
    >>> # Attribute access is forwarded to the content for convenience
    >>> m.category.upper()
    'VALID STRING'
    >>> # Generic argument types are handled by pydantic - let's try to provide a string for a Tag[int] number
    >>> m = Model(width="not_a_number", category="valid_string")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 1 validation error for Model
    width -> content
      value is not a valid integer (type=type_error.integer)
    """

    # Optional in case of self-closing tags
    content: Optional[T] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

    def __getattr__(self, item):
        """Forward attribute access to the tag's content for simplicity."""
        if item.startswith("__"):  # Don't break copy/pickle/inspection protocols
            raise AttributeError(item)
        content = self.__dict__.get("content")
        if content is None:
            raise AttributeError(
                f"{type(self).__name__} has no attribute {item!r} and its content is empty "
                f"(self-closing tag?). XML attributes, if any, are in `.attributes`: {self.attributes!r}"
            )
        return getattr(content, item)

    def __getitem__(self, key):
        return self.content[key]

    def __setitem__(self, key, value):
        self.content[key] = value

    def __str__(self):
        return "" if self.content is None else str(self.content)

    def __bool__(self):
        return self.content is not None or bool(self.attributes)

    @model_validator(mode="before")
    @classmethod
    def pre_convert(cls, value: Union[T, dict, "Tag[T]"]) -> Union["Tag[T]", Dict[str, Any]]:
        """Used to split tag's text with other xml attributes."""
        if isinstance(value, cls):
            return value

        if isinstance(value, dict):
            data = deepcopy(value)
            attributes = {snake_case(k.lstrip("@")): v for k, v in data.items() if k.startswith("@")}
            content = data.pop("#text", data) if len(attributes) != len(data) else None
            return {"content": content, "attributes": attributes}

        return {"content": value, "attributes": {}}

    @classmethod
    def flatten_tag_encoder(cls, value):
        """Encoder that translates Tag objects (dict) to plain .content values (T)."""
        if isinstance(value, XMLBaseModel):
            return value.dict_plain()
        if isinstance(value, Tag):
            return value.content

        return pydantic_encoder(value)
