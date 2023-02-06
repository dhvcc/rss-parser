import dataclasses
import json
import operator
from copy import deepcopy
from typing import TypeVar, Generic, TYPE_CHECKING

from pydantic import validator
from pydantic.generics import GenericModel

if TYPE_CHECKING:
    from pydantic import BaseModel

T = TypeVar("T")

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from dataclass_wizard import JSONWizard

deco = dataclass(frozen=True, order=True)


@deco
class TagData_(JSONWizard):
    content: str = field(compare=True)
    # attributes: dict

    @classmethod
    def from_json(cls, string, *, decoder=json.loads, **decoder_kwargs):
        print('DATA TO JSON', decoder_kwargs)
        super().from_json(string, decoder=decoder, **decoder_kwargs)


@deco
class Tag_(JSONWizard):
    c: TagData_
    # __root__: TagData_[T]
    #
    # if TYPE_CHECKING:
    #     content: T
    #     attributes: dict

    @classmethod
    def from_json(cls, string, *, decoder=json.loads, **decoder_kwargs):
        print('T DATA TO JSON', decoder_kwargs)
        super().from_json(string, decoder=decoder, **decoder_kwargs)


# v = Tag_.from_json('{"__root__": {"c": {"content": "123"}}}')


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

    >>> class Model(BaseModel):
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
    """
    __root__: TagData[T]

    if TYPE_CHECKING:
        content: T
        attributes: dict

    @validator('__root__', pre=True, always=True)
    def validate_attributes(cls, v: T | dict, values, **kwargs):  # noqa
        """Used to split tag's text with other xml attributes."""
        if isinstance(v, dict):
            data = deepcopy(v)
            return {'content': data.pop('#text', ''), 'attributes': data}
        return {'content': v, 'attributes': {}}

    def __getattr__(self, item):
        """Forward attribute lookup to the actual element which is stored in self.__root__."""
        # Not using super, since there's no getattr in any of the parents
        return getattr(self.__root__, item)

    def __str__(self):
        return str(self.content)

    def __int__(self):
        v = self.content
        if not isinstance(v, int):
            return int(v)
        return v

    def __float__(self):
        v = self.content
        if not isinstance(v, float):
            return float(v)
        return v

    def __bool__(self):
        return bool(self.content)

    def __eq__(self, other):
        return self.content == other

    def __lt__(self, other):
        return self.content < other

    def __gt__(self, other):
        return self.content < other

    def __add__(self, other):
        return self.content + other

    # TODO: add eq, lt, gt, bool, add, ...
