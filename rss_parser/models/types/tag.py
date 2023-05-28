import warnings
from copy import deepcopy
from json import loads
from math import ceil, floor, trunc
from operator import add, eq, floordiv, ge, gt, index, invert, le, lt, mod, mul, ne, neg, pos, pow, sub, truediv
from typing import Generic, Optional, Type, TypeVar, Union

from pydantic import create_model
from pydantic.generics import GenericModel
from pydantic.json import pydantic_encoder

from rss_parser.models import XMLBaseModel

T = TypeVar("T")


class TagExperimental(GenericModel, Generic[T]):
    """
    Class to represent XML tag.

    For example, this tag <tag>123</tag> will result in 'tag': '123' in parent dict.
    However, if we add any attributes to it <tag someAttr="val">123</tag>,
    then the value will not be '123', but {'@someAttr':'val','#text': '123'}.
    This class allows you to handle this dynamically.

    >>> from rss_parser.models import XMLBaseModel
    >>> class Model(XMLBaseModel):
    ...     number: Tag[int]
    ...     string: Tag[str]
    >>> m = Model(number=1, string={'@customAttr': 'v', '#text': 'str tag value'})
    >>> m.number.content
    1
    >>> m.number + 10  # forwarding operators to m.number.content for simplicity
    11
    >>> m.number.bit_length()  # forwarding getattr to m.number.content
    1
    >>> type(m.number), type(m.number.content)  # types are NOT the same, however, the interfaces are similar
    (<class 'rss_parser.models.image.Tag[int]'>, <class 'int'>)
    >>> m.number.attributes
    {}
    >>> m.string.content
    'str tag value'
    >>> m.string.attributes
    {'customAttr': 'v'}
    >>> m = Model(number='not_a_number', string={'@customAttr': 'v', '#text': 'str tag value'})
    Traceback (most recent call last):
     ...
    pydantic.error_wrappers.ValidationError: 1 validation error for Model
    number -> content
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
            attributes = {k.lstrip("@"): v for k, v in data.items() if k.startswith("@")}
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

        return pydantic_encoder(v)


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
    Tag: Type[TagExperimental] = create_model(
        "Tag",
        __base__=(TagExperimental, Generic[T]),
        **{method: _make_proxy_operator(operator) for method, operator in _OPERATOR_MAPPING.items()},
    )
