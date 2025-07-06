from typing import Generic, TypeVar, Union

from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic_validators = import_v1_pydantic(".validators")

T = TypeVar("T")


class OnlyList(list, Generic[T]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        yield pydantic_validators.list_validator

    @classmethod
    def validate(cls, v: Union[dict, list]):
        if isinstance(v, list):
            return cls(v)
        return cls([v])

    def __repr__(self):
        return f"OnlyList({super().__repr__()})"
