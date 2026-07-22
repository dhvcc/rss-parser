from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict

from rss_parser.models.utils import camel_case


def _plainify(value: Any, dumped: Any) -> Any:
    """Walk the model and its dump in parallel, flattening every Tag into its content."""
    from rss_parser.models.types.tag import Tag  # noqa: PLC0415

    if isinstance(value, Tag):
        if isinstance(dumped, dict) and set(dumped) == {"content", "attributes"}:
            dumped = dumped["content"]
        return _plainify(value.content, dumped)
    if isinstance(value, BaseModel):
        result = {}
        for name in type(value).model_fields:
            if name in dumped:  # respects include/exclude kwargs
                result[name] = _plainify(getattr(value, name), dumped[name])
        for name in value.model_extra or {}:
            if name in dumped:
                result[name] = dumped[name]
        return result
    if isinstance(value, (list, tuple)):
        return [_plainify(item, dumped_item) for item, dumped_item in zip(value, dumped)]
    return dumped


class XMLBaseModel(BaseModel):
    """
    Base model for all XML-backed schemas.

    - Aliases are generated in camelCase to match common XML tag naming (``pub_date`` -> ``pubDate``).
    - Fields can also be populated by their python names, which is handy in tests and fixtures.
    - Unknown tags are *kept*, not discarded: anything that is not declared on the schema
      (e.g. ``itunes:keywords`` on a bare RSS schema) is stored on the model and is accessible
      via ``model_extra``.
    """

    model_config = ConfigDict(
        alias_generator=camel_case,
        populate_by_name=True,
        extra="allow",
    )

    def dict_plain(self, **kwargs) -> dict:
        """
        Like ``model_dump(mode="json")``, but every Tag is flattened into its plain
        content value, dropping the content/attributes structure.
        """
        return _plainify(self, self.model_dump(mode="json", **kwargs))

    def json_plain(self, **kwargs) -> str:
        """
        Serialize the model to JSON while flattening Tag instances into their content.
        """
        return json.dumps(self.dict_plain(**kwargs), ensure_ascii=False)


__all__ = ("XMLBaseModel",)
