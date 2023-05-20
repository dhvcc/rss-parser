from re import sub
from typing import TYPE_CHECKING, Type, get_type_hints

if TYPE_CHECKING:
    from rss_parser.models.types.tag import Tag


def camel_case(s):
    s = sub(r"([_\-])+", " ", s).title().replace(" ", "")
    return "".join([s[0].lower(), s[1:]])


def extract_tag_sub_type(tag_type: Type["Tag"]):
    return extract_sub_type(tag_type.__fields__["__root__"].type_)


def extract_sub_type(type_):
    return get_type_hints(type_)["content"]
