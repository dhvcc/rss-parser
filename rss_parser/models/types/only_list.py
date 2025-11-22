from __future__ import annotations

from typing import Annotated, Generic, TypeVar

from pydantic.functional_validators import AfterValidator, BeforeValidator

T = TypeVar("T")


class OnlyList(list, Generic[T]):
    @staticmethod
    def _ensure_list(value):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return [value]

    @classmethod
    def _as_only_list(cls, value):
        if isinstance(value, cls):
            return value
        return cls(value)

    def __repr__(self):
        return f"OnlyList({super().__repr__()})"

    def __class_getitem__(cls, item):
        return Annotated[
            list[item],
            BeforeValidator(cls._ensure_list),
            AfterValidator(cls._as_only_list),
        ]
