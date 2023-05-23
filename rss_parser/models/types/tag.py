import warnings
from copy import deepcopy
from math import ceil, floor, trunc
from operator import add, eq, floordiv, ge, gt, index, invert, le, lt, mod, mul, ne, neg, pos, pow, sub, truediv
from typing import TYPE_CHECKING, Generic, Type, TypeVar, Union

from pydantic import create_model, validator
from pydantic.generics import GenericModel

T = TypeVar("T")


class TagData(GenericModel, Generic[T]):
    content: T
    attributes: dict


class TagRaw(GenericModel, Generic[T]):
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
        """Optionally forward attribute lookup to the actual element which is stored in self.__root__."""
        return getattr(self.__root__, item)

    @classmethod
    def is_tag(cls, type_):
        # Issubclass doesn't work with Unions and stuff, so this is the best way to compare
        return type(type_) is type(cls) and issubclass(type_, cls)


_OPERATOR_MAPPING = {
    # Unary
    "__pos__": pos,
    "__neg__": neg,
    "__abs__": abs,
    "__invert__": invert,
    "__round__": round,
    "__floor__": floor,
    "__ceil__": ceil,
    # Conversion
    "__str__": str,
    "__int__": int,
    "__float__": float,
    "__bool__": bool,
    "__complex__": complex,
    "__oct__": oct,
    "__hex__": hex,
    "__index__": index,
    "__trunc__": trunc,
    # Comparison
    "__lt__": lt,
    "__gt__": gt,
    "__le__": le,
    "__eq__": eq,
    "__ne__": ne,
    "__ge__": ge,
    # Arithmetic
    "__add__": add,
    "__sub__": sub,
    "__mul__": mul,
    "__truediv__": truediv,
    "__floordiv__": floordiv,
    "__mod__": mod,
    "__pow__": pow,
}


def _make_proxy_operator(operator):
    def f(self, *args):
        return operator(self.content, *args)

    f.__name__ = operator.__name__

    return f


with warnings.catch_warnings():
    # Ignoring pydantic's warnings when inserting dunder methods (this is not a field so we don't care)
    warnings.filterwarnings("ignore", message="fields may not start with an underscore")
    Tag: Type[TagRaw] = create_model(
        "Tag",
        __base__=(TagRaw, Generic[T]),
        **{method: _make_proxy_operator(operator) for method, operator in _OPERATOR_MAPPING.items()},
    )
