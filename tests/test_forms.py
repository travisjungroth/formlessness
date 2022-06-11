from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Optional

import jsonschema
import pytest

from formlessness.constraints import constraint
from formlessness.constraints import is_str
from formlessness.deserializers import KwargsDeserializer
from formlessness.exceptions import FormErrors
from formlessness.fields import DateField
from formlessness.fields import StrField
from formlessness.forms import BasicForm
from formlessness.sections import BasicSection
from formlessness.serializers import serializer
from formlessness.types import JSONDict


@dataclass
class Film:
    title: str
    release_date: date
    distributor: str
    green_light_date: Optional[date] = None
    director: Optional[str] = None
    location: Optional[Location] = None


@dataclass
class Location:
    city: str
    country: str


@constraint("Green light date must be before release date if set.")
def green_light_before_release(film: Film):
    return film.green_light_date is None or film.green_light_date < film.release_date


@constraint("Must be 140 characters or less.", requires=[is_str])
def lte_140_characters(s: str):
    return len(s) <= 140


@constraint("Must not be a Sunday.")
def not_sunday(day: date):
    return day.weekday() != 6


@pytest.fixture
def form() -> BasicForm[Film]:
    return BasicForm(
        label="Favorite Film",
        description="If you had to pick one.",
        extra_object_constraints=[green_light_before_release],
        serializer=serializer(asdict),
        deserializer=KwargsDeserializer(Film, "Can't make a Film from the given data."),
        children=[
            StrField(
                label="Title",
                extra_data_constraints=[lte_140_characters],
                extra_object_constraints=[lte_140_characters],
            ),
            DateField(
                label="Released",
                description="Date of US release.",
                extra_object_constraints=[not_sunday],
                key="release_date",
            ),
            BasicSection(
                label="Optional Film Details",
                collapsable=True,
                collapsed=True,
                children=[
                    DateField(
                        label="Green Light Date",
                        required=False,
                        nullable=True,
                    ),
                    StrField(
                        label="Director",
                        required=False,
                        nullable=True,
                    ),
                    BasicForm(
                        label="Location",
                        serializer=serializer(asdict),
                        deserializer=KwargsDeserializer(Location),
                        nullable=True,
                        children=[StrField(label="City"), StrField(label="Country")],
                    ),
                ],
            ),
            StrField(
                label="Distributor",
                default="Netflix",
                required=False,
            ),
        ],
    )


@pytest.fixture
def form_data(film) -> JSONDict:
    return {
        "title": "The King",
        "release_date": "2021-10-09",
        "green_light_date": "2017-05-05",
        "location": {"city": "Eastcheap", "country": "England"},
    }


@pytest.fixture
def film() -> Film:
    return Film(
        title="The King",
        release_date=date(2021, 10, 9),
        green_light_date=date(2017, 5, 5),
        location=Location("Eastcheap", "England"),
        distributor="Netflix",
    )


def test_make_object(form, form_data, film):
    """
    Form.make_object is the main interface to the whole thing,
    to go from data to an object and do all the validation.
    """
    obj = form.make_object(form_data)
    assert obj == film
    form_data["release_date"] = date(2022, 1, 1)  # noqa
    with pytest.raises(FormErrors):
        form.make_object(form_data)


def test_issues(form):
    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        "location": {"city": "Eastcheap", "country": "England"},
        "distributor": "Netflix",
    }
    assert form.validate_data(data)
    obj = form.deserialize(data)
    assert form.validate_object(obj)

    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        "green_light_date": "2017-05-05",
        "location": {"city": "Eastcheap", "country": "England"},
        "distributor": "Netflix",
    }
    assert form.validate_data(data)
    obj = form.deserialize(data)
    assert form.validate_object(obj)

    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        # green light after release, should return an issue
        "green_light_date": "2022-05-05",
        "location": {"city": "Eastcheap", "country": "England"},
        "distributor": "Netflix",
    }
    # This could be checked at the data stage, but it's not in this example.
    assert form.validate_data(data)
    obj = form.deserialize(data)
    assert not form.validate_object(obj)

    data = {
        "title": "The King",
        "release_date": 20211009,
        "location": {"city": "Eastcheap", "country": "England"},
        "distributor": "Netflix",
    }
    assert not form.validate_data(data)

    data = {
        "title": "The King",
        "release_date": "2021-10-10",  # Sunday check
        "location": {"city": "Eastcheap", "country": "England"},
        "distributor": "Netflix",
    }
    assert form.validate_data(data)
    obj = form.deserialize(data)
    print(obj.release_date.weekday())
    assert not form.validate_object(obj)


def test_display(form):
    expected = {
        "type": "form",
        "label": "Favorite Film",
        "collapsable": False,
        "collapsed": False,
        "description": "If you had to pick one.",
        "objectPath": "",
        "contents": [
            {
                "type": "field",
                "label": "Title",
                "widget": {"type": "text"},
                "objectPath": "/title",
            },
            {
                "type": "field",
                "label": "Released",
                "description": "Date of US release.",
                "widget": {"type": "date_picker"},
                "objectPath": "/release_date",
            },
            {
                "type": "section",
                "label": "Optional Film Details",
                "collapsable": True,
                "collapsed": True,
                "contents": [
                    {
                        "type": "field",
                        "label": "Green Light Date",
                        "widget": {"type": "date_picker"},
                        "objectPath": "/green_light_date",
                    },
                    {
                        "type": "field",
                        "label": "Director",
                        "widget": {"type": "text"},
                        "objectPath": "/director",
                    },
                    {
                        "label": "Location",
                        "objectPath": "/location",
                        "type": "form",
                        "collapsable": False,
                        "collapsed": False,
                        "contents": [
                            {
                                "label": "City",
                                "objectPath": "/location/city",
                                "type": "field",
                                "widget": {"type": "text"},
                            },
                            {
                                "label": "Country",
                                "objectPath": "/location/country",
                                "type": "field",
                                "widget": {"type": "text"},
                            },
                        ],
                    },
                ],
            },
            {
                "label": "Distributor",
                "objectPath": "/distributor",
                "type": "field",
                "widget": {"type": "text"},
            },
        ],
    }
    display = form.display()
    assert display == expected


validate_json = partial(
    jsonschema.validate, format_checker=jsonschema.draft7_format_checker
)


def test_display_json(form):
    with open("tests/basic_schema.json") as f:
        schema = json.load(f)
    validate_json(
        form.display(),
        schema,
    )


def test_data_schema_against_form_data(form, form_data):
    schema = form.data_schema()
    validate_json(form_data, schema)


def test_data_schema(form):
    schema = form.data_schema()
    expected = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "properties": {
            "director": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "distributor": {"type": "string"},
            "green_light_date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "location": {
                "properties": {
                    "city": {"type": "string"},
                    "country": {"type": "string"},
                },
                "required": ["city", "country"],
                "type": "object",
                "unevaluatedProperties": False,
            },
            "release_date": {"type": "string"},
            "title": {"type": "string"},
        },
        "required": ["title", "release_date", "location"],
        "type": "object",
        "unevaluatedProperties": False,
    }
    assert schema == expected
