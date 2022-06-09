import json
from dataclasses import asdict, dataclass
from datetime import date
from typing import Optional

import jsonschema
import pytest

from formlessness.constraints import constraint
from formlessness.deserializers import KwargsDeserializer
from formlessness.exceptions import FormErrors
from formlessness.fields import DateField, StrField
from formlessness.forms import BasicForm
from formlessness.sections import BasicSection
from formlessness.serializers import serializer


@dataclass
class Film:
    title: str
    release_date: date
    green_light_date: Optional[date] = None


@constraint("Green light date must be before release date if set.")
def green_light_before_release(film: Film):
    return film.green_light_date is None or film.green_light_date < film.release_date


@constraint("Must be 140 characters or less.")
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
                    ),
                ],
            ),
        ],
    )


def test_make_object(form):
    """
    Form.make_object is the main interface to the whole thing,
    to go from data to an object and do all the validation.
    """
    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        "green_light_date": "2017-05-05",
    }
    film = Film(
        title="The King",
        release_date=date(2021, 10, 9),
        green_light_date=date(2017, 5, 5),
    )
    obj = form.make_object(data)
    assert obj == film
    data["release_date"] = date(2022, 1, 1)
    with pytest.raises(FormErrors):
        form.make_object(data)


def test_issues(form):
    data = {
        "title": "The King",
        "release_date": "2021-10-09",
    }
    assert form.validate_data(data)
    obj = form.deserialize(data)
    assert form.validate_object(obj)

    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        "green_light_date": "2017-05-05",
    }
    assert form.validate_data(data)
    obj = form.deserialize(data)
    assert form.validate_object(obj)

    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        # green light after release, should return an issue
        "green_light_date": "2022-05-05",
    }
    # This could be checked at the data stage, but it's not in this example.
    assert form.validate_data(data)
    obj = form.deserialize(data)
    assert not form.validate_object(obj)

    data = {
        "title": "The King",
        "release_date": 20211009,
    }
    assert not form.validate_data(data)

    data = {
        "title": "The King",
        "release_date": "2021-10-10",  # Sunday check
    }
    assert form.validate_data(data)
    obj = form.deserialize(data)
    print(obj.release_date.weekday())
    assert not form.validate_object(obj)


def test_display(form):
    expected = {
        "type": "form",
        "label": "Favorite Film",
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
                ],
            },
        ],
    }
    display = form.display()
    assert display == expected


def test_display_json(form):
    with open("tests/basic_schema.json") as f:
        schema = json.load(f)
    jsonschema.validate(
        form.display(), schema, format_checker=jsonschema.draft7_format_checker
    )
