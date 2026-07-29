from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class Person(XMLBaseModel):
    name: Tag[str]
    "Conveys a human-readable name for the person."

    uri: Tag[str] | None = None
    "Contains a home page for the person."

    email: Tag[str] | None = None
    "Contains an email address for the person."
