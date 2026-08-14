import json

import pytest
from pydantic import BaseModel, TypeAdapter

from rss_parser.models import XMLBaseModel
from rss_parser.models.atom.atom import Atom
from rss_parser.models.atom.entry import Entry
from rss_parser.models.atom.feed import Feed
from rss_parser.models.atom.person import Person
from rss_parser.models.atom.source import Source
from rss_parser.models.rdf.channel import RDFChannel
from rss_parser.models.rdf.item import RDFItem
from rss_parser.models.rdf.rdf import RDF
from rss_parser.models.rss.channel import Channel
from rss_parser.models.rss.image import Image
from rss_parser.models.rss.item import Item
from rss_parser.models.rss.itunes import ITunesChannel, ITunesItem, ITunesOwner, Podcast
from rss_parser.models.rss.rss import RSS
from rss_parser.models.rss.skip import SkipDays, SkipHours
from rss_parser.models.rss.text_input import TextInput
from rss_parser.models.types import DateTimeOrStr, OnlyList, Tag, TextConstruct


class TestCustomTypesSchema:
    def test_datetime_or_str_schema(self):
        adapter = TypeAdapter(DateTimeOrStr)
        schema = adapter.json_schema()

        assert schema.get("type") == "string"
        assert schema.get("format") == "date-time"
        assert schema.get("examples") == ["1970-01-01T00:00:00"]
        # Must be JSON serializable
        assert json.dumps(schema)

    def test_tag_schema(self):
        class TagModel(XMLBaseModel):
            tag_str: Tag[str]
            tag_int: Tag[int]
            tag_date: Tag[DateTimeOrStr]
            tag_text: Tag[TextConstruct]

        schema = TagModel.model_json_schema()
        assert "$defs" in schema
        assert "tagStr" in schema["properties"]
        assert "tagInt" in schema["properties"]
        assert "tagDate" in schema["properties"]
        assert "tagText" in schema["properties"]
        assert json.dumps(schema)

    def test_only_list_schema(self):
        class ListModel(BaseModel):
            items: OnlyList[str]

        schema = ListModel.model_json_schema()
        assert schema["properties"]["items"]["type"] == "array"
        assert schema["properties"]["items"]["items"]["type"] == "string"
        assert json.dumps(schema)

    def test_text_construct_schema(self):
        adapter = TypeAdapter(TextConstruct)
        schema = adapter.json_schema()

        assert "anyOf" in schema
        types = [s.get("type") for s in schema["anyOf"]]
        assert "string" in types
        assert "object" in types
        assert json.dumps(schema)


class TestFeedModelsSchema:
    @pytest.mark.parametrize(
        "model_cls",
        [
            RSS[Channel[Item]],
            Podcast,
            ITunesChannel,
            ITunesItem,
            ITunesOwner,
            Atom[Feed[Entry]],
            Feed[Entry],
            Entry,
            Person,
            Source,
            RDF[RDFChannel, RDFItem],
            RDFChannel,
            RDFItem,
            Channel[Item],
            Item,
            Image,
            TextInput,
            SkipHours,
            SkipDays,
        ],
    )
    def test_model_json_schema_generation(self, model_cls):
        schema = model_cls.model_json_schema()

        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"
        assert json.dumps(schema)

    def test_rss_date_fields_in_schema(self):
        schema = Item.model_json_schema()
        assert "pubDate" in schema["properties"]
        prop = schema["properties"]["pubDate"]
        assert "anyOf" in prop
        refs = [item.get("$ref") for item in prop["anyOf"] if "$ref" in item]
        assert len(refs) == 1
        def_key = refs[0].split("/")[-1]
        assert def_key in schema["$defs"]

    def test_atom_date_fields_in_schema(self):
        schema = Entry.model_json_schema()
        assert "updated" in schema["properties"]
        assert "published" in schema["properties"]
        assert json.dumps(schema)
