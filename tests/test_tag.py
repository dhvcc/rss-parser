import pytest

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class Model(XMLBaseModel):
    width: Tag[int]
    category: Tag[str]


def make_model(**overrides):
    data = {
        "width": 48,
        "category": {"@someAttribute": "https://example.com", "#text": "valid string"},
        **overrides,
    }
    return Model.model_validate(data)


class TestContentAndAttributes:
    def test_content_is_typed(self):
        m = make_model()

        assert m.width.content == 48
        assert isinstance(m.width.content, int)

    def test_attributes_are_snake_cased_and_stripped(self):
        m = make_model()

        assert m.category.attributes == {"some_attribute": "https://example.com"}

    def test_self_closing_tag_has_no_content(self):
        m = make_model(category={"@href": "https://example.com"})

        assert m.category.content is None
        assert m.category.attributes == {"href": "https://example.com"}


class TestErgonomics:
    def test_str_returns_content(self):
        m = make_model()

        assert str(m.width) == "48"
        assert str(m.category) == "valid string"

    def test_str_of_empty_tag_is_empty(self):
        m = make_model(category={"@href": "x"})

        assert str(m.category) == ""

    def test_bool(self):
        m = make_model(category={"@href": "x"})

        assert bool(m.width)
        assert bool(m.category)  # no content, but has attributes
        assert not bool(Tag[str]())

    def test_getattr_forwards_to_content(self):
        m = make_model()

        assert m.category.upper() == "VALID STRING"

    def test_getattr_on_empty_content_mentions_self_closing_tag(self):
        m = make_model(category={"@href": "x"})

        with pytest.raises(AttributeError, match="self-closing"):
            m.category.upper()

    def test_getitem_forwards_to_content(self):
        m = make_model()

        assert m.category[:5] == "valid"


class TestDumpRoundTrip:
    def test_full_dump_round_trips(self):
        m = make_model()

        assert Model.model_validate(m.model_dump()) == m

    def test_exclude_defaults_dump_round_trips(self):
        m = make_model()
        again = Model.model_validate(m.model_dump(exclude_defaults=True))

        assert again.width.content == 48
        assert again.width.attributes == {}
        assert again.category.content == "valid string"
        assert again.category.attributes == {"some_attribute": "https://example.com"}

    def test_content_only_dict_is_kept_as_tag_shape(self):
        tag = Tag[int].model_validate({"content": 5})

        assert tag.content == 5
        assert tag.attributes == {}

    def test_attributes_must_be_a_dict_to_count_as_tag_shape(self):
        # An XML element literally named <content> with a sibling <attributes> text node
        # is not a dumped Tag - it still goes through the attribute-splitting path
        tag = Tag[dict].model_validate({"content": "x", "attributes": "y"})

        assert tag.content == {"content": "x", "attributes": "y"}
        assert tag.attributes == {}
