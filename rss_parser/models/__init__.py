from __future__ import annotations

import json
from typing import Any, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict

from rss_parser.models.utils import camel_case

TAG_SHAPE_KEYS = frozenset(("content", "attributes"))


def _dump_key(model: BaseModel, name: str, by_alias: bool) -> str:
    """Return the key under which a field appears in ``model``'s dump."""
    if not by_alias:
        return name
    field = type(model).model_fields[name]
    return field.serialization_alias or field.alias or name


def _plainify(value: Any, dumped: Any, by_alias: bool = False) -> Any:
    """Walk the model and its dump in parallel, flattening every Tag into its content."""
    from rss_parser.models.types.tag import Tag  # noqa: PLC0415

    if isinstance(value, Tag):
        if isinstance(dumped, dict) and set(dumped) <= TAG_SHAPE_KEYS:
            # Dump options such as exclude_defaults may drop "attributes" (or even "content"),
            # so any subset of the Tag shape is still a Tag dump that must be flattened
            dumped = dumped.get("content")
        return _plainify(value.content, dumped, by_alias)
    if isinstance(value, BaseModel) and isinstance(dumped, dict):
        result = {}
        for name in type(value).model_fields:
            key = _dump_key(value, name, by_alias)
            if key in dumped:  # respects include/exclude kwargs
                result[key] = _plainify(getattr(value, name), dumped[key], by_alias)
        for name in value.model_extra or {}:
            if name in dumped:
                result[name] = dumped[name]
        return result
    if isinstance(value, (list, tuple)) and isinstance(dumped, (list, tuple)):
        return [_plainify(item, dumped_item, by_alias) for item, dumped_item in zip(value, dumped)]
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
        return _plainify(self, self.model_dump(mode="json", **kwargs), kwargs.get("by_alias", False))

    def json_plain(
        self,
        *,
        indent: int | str | None = None,
        separators: tuple[str, str] | None = None,
        sort_keys: bool = False,
        ensure_ascii: bool = False,
        **kwargs,
    ) -> str:
        """
        Serialize the model to JSON while flattening Tag instances into their content.

        ``indent``, ``separators``, ``sort_keys`` and ``ensure_ascii`` are passed to
        :func:`json.dumps`; all other kwargs are dump options passed to :meth:`dict_plain`.
        """
        return json.dumps(
            self.dict_plain(**kwargs),
            indent=indent,
            separators=separators,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
        )


__all__ = ("XMLBaseModel",)
