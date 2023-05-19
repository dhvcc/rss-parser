from copy import deepcopy
from typing import TYPE_CHECKING, Generic, TypeVar, Union

from pydantic import validator
from pydantic.generics import GenericModel

T = TypeVar("T")


class TagData(GenericModel, Generic[T]):
    content: T
    attributes: dict


class Tag(GenericModel, Generic[T]):
    """
    Class to represent XML tag.

    For example, this tag <tag>123</tag> will result in 'tag': '123' in parent dict.
    However, if we add any attributes to it <tag someAttr="val">123</tag>,
    then the value will not be '123', but {'@someAttr':'val','#text': '123'}.
    This class allows you to handle this dynamically.

    >>> from rss_parser.models import RSSBaseModel
    >>> class Model(RSSBaseModel):
    ...     number: Tag[int]
    ...     string: Tag[str]
    ...
    >>> m = Model(number=1, string={'@customAttr': 'v', '#text': 'str tag value'})
    >>> m.number.content
    1
    >>> m.number.attributes
    {}
    >>> m.string.content
    'str tag value'
    >>> m.string.attributes
    {'@customAttr': 'v'}
    >>> m = Model(number='not_a_number', string={'@customAttr': 'v', '#text': 'str tag value'})
    Traceback (most recent call last):
     ...
    pydantic.error_wrappers.ValidationError: 1 validation error for Model
    number -> __root__ -> content
      value is not a valid integer (type=type_error.integer)
    """

    __root__: TagData[T]

    if TYPE_CHECKING:
        content: T
        attributes: dict

    @validator("__root__", pre=True, always=True)
    def validate_attributes(cls, v: Union[T, dict], values, **kwargs):  # noqa
        """Used to split tag's text with other xml attributes."""
        if isinstance(v, dict):
            data = deepcopy(v)
            return {"content": data.pop("#text", ""), "attributes": {k.lstrip("@"): v for k, v in data.items()}}
        return {"content": v, "attributes": {}}

    def __getattr__(self, item):
        """Forward attribute lookup to the actual element which is stored in self.__root__."""
        # Not using super, since there's no getattr in any of the parents
        try:
            return getattr(self.__root__, item)
        except AttributeError:
            return getattr(self.__root__.content, item)

    # Conversions

    def __str__(self):
        return str(self.content)

    def __int__(self):
        return int(self.content)

    def __float__(self):
        return float(self.content)

    def __bool__(self):
        return bool(self.content)

    # Comparion operators

    def __eq__(self, other):
        return self.content == other

    def __ne__(self, other) -> bool:
        return self.content != other

    def __gt__(self, other):
        return self.content > other

    def __ge__(self, other):
        return self.content >= other

    def __lt__(self, other):
        return self.content < other

    def __le__(self, other):
        return self.content <= other

    # Arithmetic  operators

    def __add__(self, other):
        return self.content + other
