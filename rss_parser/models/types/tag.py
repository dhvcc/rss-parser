from copy import deepcopy
from json import loads
from typing import Generic, Optional, TypeVar, Union

from rss_parser.models import XMLBaseModel
from rss_parser.models.utils import snake_case
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()
pydantic_generics = import_v1_pydantic(".generics")
pydantic_json = import_v1_pydantic(".json")

T = TypeVar("T")


class Tag(pydantic_generics.GenericModel, Generic[T]):
    """
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
    >>> type(m.width), type(m.width.content)
    (<class 'rss_parser.models.rss.image.Tag[int]'>, <class 'int'>)
    >>> # The attributes are empty by default
    >>> m.width.attributes
    {}
    >>> # But are populated when provided.
    >>> # Note that the @ symbol is trimmed from the beggining and name is convert to snake_case
    >>> m.category.attributes
    {'some_attribute': 'https://example.com'}
    >>> # Generic argument types are handled by pydantic - let's try to provide a string for a Tag[int] number
    >>> m = Model(width="not_a_number", category="valid_string")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: 1 validation error for Model
    width -> content
      value is not a valid integer (type=type_error.integer)
    """

    # Optional in case of self-closing tags
    content: Optional[T]
    attributes: dict

    def __getattr__(self, item):
        """Forward default getattr for content for simplicity."""
        return getattr(self.content, item)

    def __getitem__(self, key):
        return self.content[key]

    def __setitem__(self, key, value):
        self.content[key] = value

    @classmethod
    def __get_validators__(cls):
        yield cls.pre_convert
        yield cls.validate

    @classmethod
    def pre_convert(cls, v: Union[T, dict], **kwargs):  # noqa
        """Used to split tag's text with other xml attributes."""
        if isinstance(v, dict):
            data = deepcopy(v)
            attributes = {snake_case(k.lstrip("@")): v for k, v in data.items() if k.startswith("@")}
            content = data.pop("#text", data) if not len(attributes) == len(data) else None
            return {"content": content, "attributes": attributes}
        return {"content": v, "attributes": {}}

    @classmethod
    def flatten_tag_encoder(cls, v):
        """Encoder that translates Tag objects (dict) to plain .content values (T)."""
        bases = v.__class__.__bases__
        if XMLBaseModel in bases:
            # Can't pass encoder to .dict :/
            return loads(v.json_plain())
        if cls in bases:
            return v.content

        return pydantic_json.pydantic_encoder(v)
