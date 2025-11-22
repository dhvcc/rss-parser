from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from rss_parser.models.utils import camel_case


class XMLBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=camel_case)

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
