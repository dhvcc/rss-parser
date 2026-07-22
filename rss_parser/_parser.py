from enum import Enum
from typing import Any, ClassVar, Dict, Mapping, Optional, Type
from xml.parsers.expat import ExpatError

from xmltodict import parse as _xml_to_dict

from rss_parser.custom_decorators import abstract_class_attributes
from rss_parser.models import XMLBaseModel
from rss_parser.models.atom import Atom
from rss_parser.models.rdf import RDF
from rss_parser.models.rss import RSS
from rss_parser.models.rss.itunes import Podcast

# >>> FUTURE
# TODO: May be support generator based approach for big rss feeds
# TODO: Add cli to parse to json
# TODO: Older Atom versions


class FeedType(str, Enum):
    RSS = "rss"
    "RSS 0.9x / 2.0 - <rss> root element."

    ATOM = "atom"
    "Atom 1.0 - <feed> root element."

    RDF = "rdf"
    "RSS 1.0 (RDF Site Summary) - <rdf:RDF> root element."


class UnknownFeedTypeError(ValueError):
    """Raised when the feed type cannot be detected from the XML root element."""


class InvalidXMLError(ValueError):
    """Raised when the data is not well-formed XML. The original ExpatError is available as __cause__."""


@abstract_class_attributes("schema")
class BaseParser:
    """Parser for rss/atom/rdf files."""

    schema: ClassVar[Type[XMLBaseModel]]
    root_key: ClassVar[Optional[str]] = None

    @staticmethod
    def to_xml(data: str, *args, **kwargs) -> Dict[str, Any]:
        try:
            return _xml_to_dict(str(data), *args, **kwargs)
        except ExpatError as e:
            raise InvalidXMLError(f"data is not well-formed XML: {e}") from e

    @classmethod
    def parse(
        cls,
        data: str,
        *,
        schema: Optional[Type[XMLBaseModel]] = None,
        root_key: Optional[str] = None,
    ) -> XMLBaseModel:
        """
        Parse XML data into schema.
        :param data: string of XML data that needs to be parsed
        :param schema: override the parser's default schema
        :param root_key: override the parser's default root key
        :return: "schema" object
        """
        return cls.parse_dict(cls.to_xml(data), schema=schema, root_key=root_key)

    @classmethod
    def parse_dict(
        cls,
        root: Mapping[str, Any],
        *,
        schema: Optional[Type[XMLBaseModel]] = None,
        root_key: Optional[str] = None,
    ) -> XMLBaseModel:
        """Parse an already xmltodict-converted mapping into schema."""
        schema = schema if schema else cls.schema
        root_key = root_key if root_key else cls.root_key

        if root_key:
            root = root.get(root_key, root)

        return schema.model_validate(root)


class RSSParser(BaseParser):
    """RSS 0.9x / 2.0 parser."""

    root_key = "rss"
    schema = RSS


class AtomParser(BaseParser):
    """Atom 1.0 parser."""

    schema = Atom


class RDFParser(BaseParser):
    """RSS 1.0 (RDF Site Summary) parser."""

    root_key = "rdf:RDF"
    schema = RDF

    @classmethod
    def parse_dict(
        cls,
        root: Mapping[str, Any],
        *,
        schema: Optional[Type[XMLBaseModel]] = None,
        root_key: Optional[str] = None,
    ) -> XMLBaseModel:
        if root_key is None:
            # The rdf namespace prefix is not guaranteed to be "rdf" - find the actual root key
            root_key = next(
                (key for key in root if key.lower() == "rdf" or key.lower().endswith(":rdf")),
                cls.root_key,
            )
        return super().parse_dict(root, schema=schema, root_key=root_key)


class PodcastParser(RSSParser):
    """RSS 2.0 parser with Apple Podcasts (itunes:*) extensions."""

    schema = Podcast


DEFAULT_PARSERS: Dict[FeedType, Type[BaseParser]] = {
    FeedType.RSS: RSSParser,
    FeedType.ATOM: AtomParser,
    FeedType.RDF: RDFParser,
}


def _detect_feed_type_from_root(root: Mapping[str, Any]) -> FeedType:
    for key in root:
        lowered = key.lower()
        if lowered == "rss":
            return FeedType.RSS
        if lowered == "feed":
            return FeedType.ATOM
        if lowered == "rdf" or lowered.endswith(":rdf"):
            return FeedType.RDF

    raise UnknownFeedTypeError(
        f"Could not detect the feed type from root element(s) {sorted(root)}. "
        "Supported roots are <rss> (RSS 0.9x/2.0), <feed> (Atom 1.0) and <rdf:RDF> (RSS 1.0). "
        "If your document uses a custom root, parse it with an explicit parser, e.g. "
        "RSSParser.parse(data, schema=..., root_key=...)"
    )


def detect_feed_type(data: str) -> FeedType:
    """
    Detect the feed type from the XML root element.

    :raises UnknownFeedTypeError: if the root element is not a known feed root
    """
    return _detect_feed_type_from_root(BaseParser.to_xml(data))


def parse(
    data: str,
    *,
    parsers: Optional[Mapping[FeedType, Type[BaseParser]]] = None,
) -> XMLBaseModel:
    """
    Parse any supported feed, detecting the feed type from the XML root element.

    Returns an ``RSS``, ``Atom`` or ``RDF`` model depending on the detected type.

    :param data: string of XML data that needs to be parsed
    :param parsers: optionally override the parser used for a feed type,
        e.g. ``parse(data, parsers={FeedType.RSS: PodcastParser})``
    :raises UnknownFeedTypeError: if the root element is not a known feed root
    """
    parser_map: Dict[FeedType, Type[BaseParser]] = {**DEFAULT_PARSERS, **(parsers or {})}
    root = BaseParser.to_xml(data)
    feed_type = _detect_feed_type_from_root(root)
    return parser_map[feed_type].parse_dict(root)
