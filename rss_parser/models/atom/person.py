from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag
from rss_parser.pydantic_proxy import import_v1_pydantic

pydantic = import_v1_pydantic()


class Person(XMLBaseModel):
    name: Tag[str]
    "Conveys a human-readable name for the person."

    uri: Optional[Tag[str]] = None
    "Contains a home page for the person."

    email: Optional[Tag[str]] = None
    "Contains an email address for the person."
