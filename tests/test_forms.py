import json
from dataclasses import asdict, dataclass
from datetime import date
from typing import Optional

import pytest

from formlessness.deserializers import KwargsDeserializer
from formlessness.exceptions import ValidationIssueMap
from formlessness.fields import DateField, StrField
from formlessness.forms import BasicForm
from formlessness.sections import BasicSection
from formlessness.serializers import serializer
from formlessness.validators import validator


@dataclass
class Film:
    title: str
    release_date: date
    green_light_date: Optional[date] = None


@validator("Green light date must be before release date if set.")
def green_light_before_release(film: Film):
    return film.green_light_date is None or film.green_light_date < film.release_date


@validator("Must be 140 characters or less.")
def lte_140_characters(s: str):
    return len(s) <= 140


@validator("Must not be a Sunday.")
def not_sunday(day: date):
    return day.weekday() != 6


@pytest.fixture
def form() -> BasicForm[Film]:
    return BasicForm(
        label="Favorite Film",
        description="If you had to pick one.",
        extra_object_validators=[green_light_before_release],
        serializer=serializer(asdict),
        deserializer=KwargsDeserializer(Film, "Can't make a Film from the given data."),
        children=[
            StrField(
                label="Title",
                extra_data_validators=[lte_140_characters],
                extra_object_validators=[lte_140_characters],
            ),
            DateField(
                label="Released",
                description="Date of US release.",
                extra_object_validators=[not_sunday],
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
    with pytest.raises(ValidationIssueMap):
        form.make_object(data)


def test_issues(form):
    data = {
        "title": "The King",
        "release_date": "2021-10-09",
    }
    assert not form.data_issues(data)

    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        "green_light_date": "2017-05-05",
    }
    assert not form.data_issues(data)
    obj = form.deserialize(data)
    assert not form.object_issues(obj)

    data = {
        "title": "The King",
        "release_date": "2021-10-09",
        "green_light_date": "2022-05-05",
    }
    assert not form.data_issues(data)
    obj = form.deserialize(data)
    assert form.object_issues(obj)

    data = {
        "title": "The King",
        "release_date": 20211009,
    }
    assert form.data_issues(data)


def test_display(form):
    expected = {
        "type": "form",
        "label": "Favorite Film",
        "description": "If you had to pick one.",
        "sub_forms": {
            "title": {
                "type": "field",
                "label": "Title",
                "widget": "text_box",
                "value": "The King",
            },
            "release_date": {
                "type": "field",
                "label": "Released",
                "description": "Date of US release.",
                "widget": "date_selector",
            },
            "optional_film_details": {
                "type": "section",
                "label": "Optional Film Details",
                "collapsable": True,
                "collapsed": True,
                "sub_forms": {
                    "green_light_date": {
                        "type": "field",
                        "label": "Green Light Date",
                        "widget": "date_selector",
                        "value": "2017-05-05",
                    },
                },
            },
        },
    }
    display = form.display({"title": "The King", "green_light_date": "2017-05-05"})
    assert display == expected
    assert json.dumps(display) == json.dumps(expected)
