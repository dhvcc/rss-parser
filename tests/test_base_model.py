from typing import Optional, Type, Union

from rss_parser.models import RSSBaseModel
from rss_parser.models.types.tag import Tag


class Model(RSSBaseModel):
    number: int
    opt_number: Optional[int]
    number_string: Union[int, str]


model_field_count = len([f for f in Model.__fields__.values()])


def count_tag_fields(model: Type[Model]):
    return len([f for f in model.__fields__.values() if Tag.is_tag(f.type_)])


def test_wrap_unwrap_chain_applies():
    assert count_tag_fields(Model) == 0
    assert count_tag_fields(Model.wrap_tags("__all__")) == model_field_count
    assert count_tag_fields(Model.wrap_tags("__all__").unwrap_tags("__all__")) == 0
    assert count_tag_fields(Model.wrap_tags("__all__").unwrap_tags("number")) == model_field_count - 1


def test_unwrap_populates():
    kwargs = {
        "number": 123,
        "opt_number": None,
        "numberString": "number_string",
    }
    result = {
        "number": 123,
        "opt_number": None,
        "number_string": "number_string",
    }
    obj = Model.unwrap_tags("__all__")(**kwargs)
    assert obj
    assert obj.number
    assert not obj.opt_number
    assert obj.number_string
    assert obj.dict() == result


def test_wrap_populates():
    kwargs = {
        "number": 123,
        "numberString": "number_string",
    }
    result = {
        "number": {
            "content": 123,
            "attributes": {},
        },
        "opt_number": None,
        "number_string": {
            "content": "number_string",
            "attributes": {},
        },
    }
    obj = Model.wrap_tags("__all__")(**kwargs)
    assert obj
    assert obj.number
    assert not obj.opt_number
    assert obj.number_string
    assert obj.dict() == result
