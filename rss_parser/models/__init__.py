from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from rss_parser.models.utils import camel_case


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

    def json_plain(self, **kwargs) -> str:
        """
        Serialize the model while flattening Tag instances into their content.
        """
        from rss_parser.models.types.tag import Tag  # noqa: PLC0415

        return self.model_dump_json(fallback=Tag.flatten_tag_encoder, **kwargs)

    def dict_plain(self, **kwargs):
        from rss_parser.models.types.tag import Tag  # noqa: PLC0415

        return self.model_dump(mode="json", fallback=Tag.flatten_tag_encoder, **kwargs)


__all__ = ("XMLBaseModel",)
