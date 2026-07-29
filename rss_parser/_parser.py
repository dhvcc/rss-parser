from collections.abc import Mapping
from enum import Enum
from typing import Any, ClassVar
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
# TODO: Older Atom versions


ENTITIES_DISABLED_MESSAGE = "entities are disabled"
"The exact message xmltodict raises when a document declares DTD entities."


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
    """
    Raised when the data is not well-formed XML. The original ExpatError is available as __cause__.

    A document that is well-formed but declares DTD entities raises EntitiesDisabledError instead.
    """


class EntitiesDisabledError(ValueError):
    """
    Raised when the document declares DTD entities, which are refused before expansion.

    Such a document is well-formed XML, so this is *not* an :class:`InvalidXMLError`;
    both subclass ``ValueError``.

    Note that xmltodict raises a bare ``ValueError`` from inside an expat callback, so the only
    way to recognize it is by its message (``ENTITIES_DISABLED_MESSAGE``). If upstream ever
    rewords it, the refusal degrades to a plain ``ValueError`` - the document is still rejected
    and never expanded, but this class stops being raised. ``tests/test_errors.py`` pins it.
    """


@abstract_class_attributes("schema")
class BaseParser:
    """Parser for rss/atom/rdf files."""

    schema: ClassVar[type[XMLBaseModel]]
    root_key: ClassVar[str | None] = None

    @staticmethod
    def to_xml(data: str | bytes, *args, **kwargs) -> dict[str, Any]:
        # bytes are passed through untouched so that the document's own <?xml encoding=...?>
        # declaration is honored - decoding them here would force a guess and mangle any
        # feed that is not UTF-8
        if not isinstance(data, (str, bytes)):
            data = str(data)
        try:
            return _xml_to_dict(data, *args, **kwargs)
        except ExpatError as e:
            raise InvalidXMLError(f"data is not well-formed XML: {e}") from e
        except ValueError as e:
            # xmltodict refuses DTD entities from inside an expat callback with a bare
            # ValueError - give it a type, keeping the message byte-identical
            if str(e) == ENTITIES_DISABLED_MESSAGE:
                raise EntitiesDisabledError(ENTITIES_DISABLED_MESSAGE) from e
            raise

    @classmethod
    def parse(
        cls,
        data: str | bytes,
        *,
        schema: type[XMLBaseModel] | None = None,
        root_key: str | None = None,
    ) -> XMLBaseModel:
        """
        Parse XML data into schema.
        :param data: XML data as str or bytes - bytes keep the document's own encoding declaration
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
        schema: type[XMLBaseModel] | None = None,
        root_key: str | None = None,
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


def _strip_key_prefix(value: Any, prefix: str) -> Any:
    """Recursively strip a namespace prefix (e.g. ``atom:``) from mapping keys."""
    if isinstance(value, Mapping):
        return {
            (key[len(prefix) :] if key.startswith(prefix) else key): _strip_key_prefix(item, prefix)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_strip_key_prefix(item, prefix) for item in value]
    return value


class AtomParser(BaseParser):
    """Atom 1.0 parser."""

    schema = Atom

    @classmethod
    def parse_dict(
        cls,
        root: Mapping[str, Any],
        *,
        schema: type[XMLBaseModel] | None = None,
        root_key: str | None = None,
    ) -> XMLBaseModel:
        if root_key is None:
            # The Atom namespace may be bound to a prefix (e.g. <atom:feed>) - in that case
            # every Atom element carries the prefix, so normalize it away to match the schema
            feed_key = next((key for key in root if key.lower().endswith(":feed")), None)
            if feed_key is not None:
                prefix = feed_key[: -len("feed")]
                root = {
                    ("feed" if key == feed_key else key): (
                        _strip_key_prefix(value, prefix) if key == feed_key else value
                    )
                    for key, value in root.items()
                }
        return super().parse_dict(root, schema=schema, root_key=root_key)


class RDFParser(BaseParser):
    """RSS 1.0 (RDF Site Summary) parser."""

    root_key = "rdf:RDF"
    schema = RDF

    @classmethod
    def parse_dict(
        cls,
        root: Mapping[str, Any],
        *,
        schema: type[XMLBaseModel] | None = None,
        root_key: str | None = None,
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


DEFAULT_PARSERS: dict[FeedType, type[BaseParser]] = {
    FeedType.RSS: RSSParser,
    FeedType.ATOM: AtomParser,
    FeedType.RDF: RDFParser,
}


def _detect_feed_type_from_root(root: Mapping[str, Any]) -> FeedType:
    for key in root:
        lowered = key.lower()
        if lowered == "rss":
            return FeedType.RSS
        if lowered == "feed" or lowered.endswith(":feed"):
            return FeedType.ATOM
        if lowered == "rdf" or lowered.endswith(":rdf"):
            return FeedType.RDF

    raise UnknownFeedTypeError(
        f"Could not detect the feed type from root element(s) {sorted(root)}. "
        "Supported roots are <rss> (RSS 0.9x/2.0), <feed> (Atom 1.0) and <rdf:RDF> (RSS 1.0). "
        "If your document uses a custom root, parse it with an explicit parser, e.g. "
        "RSSParser.parse(data, schema=..., root_key=...)"
    )


def detect_feed_type(data: str | bytes) -> FeedType:
    """
    Detect the feed type from the XML root element.

    :raises UnknownFeedTypeError: if the root element is not a known feed root
    """
    return _detect_feed_type_from_root(BaseParser.to_xml(data))


def parse(
    data: str | bytes,
    *,
    parsers: Mapping[FeedType, type[BaseParser]] | None = None,
) -> XMLBaseModel:
    """
    Parse any supported feed, detecting the feed type from the XML root element.

    Returns an ``RSS``, ``Atom`` or ``RDF`` model depending on the detected type.

    :param data: XML data as str or bytes - bytes keep the document's own encoding declaration
    :param parsers: optionally override the parser used for a feed type,
        e.g. ``parse(data, parsers={FeedType.RSS: PodcastParser})``
    :raises UnknownFeedTypeError: if the root element is not a known feed root
    """
    parser_map: dict[FeedType, type[BaseParser]] = {**DEFAULT_PARSERS, **(parsers or {})}
    root = BaseParser.to_xml(data)
    feed_type = _detect_feed_type_from_root(root)
    return parser_map[feed_type].parse_dict(root)
