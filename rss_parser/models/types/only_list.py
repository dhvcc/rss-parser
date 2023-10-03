from typing import List, Union

from pydantic.validators import list_validator


class OnlyList(List):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        yield list_validator

    @classmethod
    def validate(cls, v: Union[dict, list]):
        if isinstance(v, dict):
            return [v]
        return v

    def __repr__(self):
        return f"OnlyList({super().__repr__()})"
