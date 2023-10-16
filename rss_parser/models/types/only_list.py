from typing import List, TypeVar, Union

T = TypeVar("T")


class OnlyList(List[T]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        # yield list_validator

    @classmethod
    def validate(cls, v: Union[dict, list]):
        if isinstance(v, dict):
            return [v]
        return v

    def __repr__(self):
        return f"OnlyList({super().__repr__()})"
