import json
from dataclasses import asdict, dataclass
from datetime import date
from typing import Optional

import pytest

from formlessness.deserializers import KwargsDeserializer
from formlessness.fields import DateField, StrField
from formlessness.forms import BasicForm
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
        key="Favorite Film",
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
            DateField(
                label="Green Light Date",
                required=False,
            ),
        ],
    )


def test_form(form):
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
        "children": {
            "title": {"label": "Title", "widget": "text_box", "value": "The King"},
            "release_date": {
                "label": "Released",
                "description": "Date of US release.",
                "widget": "date_selector",
                "value": "2021-10-09",
            },
            "green_light_date": {
                "label": "Green Light Date",
                "widget": "date_selector",
            },
        }
    }
    display = form.display({"title": "The King", "release_date": "2021-10-09"})
    assert display == expected
    assert json.dumps(display) == json.dumps(expected)
