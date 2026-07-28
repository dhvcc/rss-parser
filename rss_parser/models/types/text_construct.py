from __future__ import annotations

from typing import Annotated, Any, Dict, Mapping, Union

from pydantic.functional_validators import BeforeValidator


def drop_attribute_keys(value: Any) -> Any:
    """
    Keep an Atom text construct as-is, dropping the ``@``-prefixed keys Tag already extracted.

    RFC 4287 3.1 allows ``type="xhtml"``, whose body is inline XHTML markup rather than escaped
    text, so xmltodict hands the field a mapping of the child elements instead of a string. That
    mapping is what you get - see :data:`TextConstruct`.

    >>> drop_attribute_keys("plain text")
    'plain text'
    >>> drop_attribute_keys({"@type": "xhtml", "div": {"p": "hi"}})
    {'div': {'p': 'hi'}}
    """
    if isinstance(value, Mapping):
        return {key: item for key, item in value.items() if not key.startswith("@")}
    return value


TextConstruct = Annotated[Union[str, Dict[str, Any]], BeforeValidator(drop_attribute_keys)]
"""
An Atom text construct: ``str`` for ``type="text"`` (the default) and ``type="html"``, and the
xmltodict mapping of the child elements for ``type="xhtml"``. Read ``.attributes["type"]`` to tell
them apart.

The xhtml case is **not** re-serialized to markup, because xmltodict cannot round-trip
mixed content: it collapses every text run of an element into a single ``#text`` value and emits
child elements before it, so ``<p>Read <a>the docs</a> before shipping.</p>`` would come back as
``<p><a>the docs</a>Read  before shipping.</p>``. Silently reordered prose is worse than a
structure the caller can see is structural, so the mapping is handed over unchanged.
"""
