from dataclasses import dataclass

import pytest

from formlessness.constraints import LE
from formlessness.constraints import FunctionConstraint
from formlessness.deserializers import KwargsDeserializer
from formlessness.exceptions import FormErrors
from formlessness.fields import IntField, StrField
from formlessness.forms import BasicForm
from formlessness.forms import VariableListForm
from tests.test_basic_form import Film


@pytest.fixture
def list_of_ints_form():
    return VariableListForm(
        IntField(key="*", extra_data_constraints=[LE(100)]),
        label="Numbers",
        extra_data_constraints=[FunctionConstraint(lambda x: len(x) < 4)],
    )


def test_list_of_ints_make_object_good(list_of_ints_form):
    data = [0, 1, 3]
    obj = list_of_ints_form.make_object(data)
    assert data == obj


def test_list_of_ints_make_object_inner_constraint(list_of_ints_form):
    data = [1, 101, 2]
    with pytest.raises(FormErrors):
        list_of_ints_form.make_object(data)


def test_list_of_ints_make_object_outer_constraint(list_of_ints_form):
    data = [1, 2, 3, 4, 5]
    with pytest.raises(FormErrors):
        list_of_ints_form.make_object(data)


def test_list_of_ints_serialize(list_of_ints_form):
    obj = [1, 2, 3, 4, 5]
    assert list_of_ints_form.serialize(obj) == obj


@dataclass
class Place:
    city: str
    country: str


@pytest.fixture
def list_of_places_form():
    return VariableListForm(
        label="Places",
        content=BasicForm(
            key="*",
            deserializer=KwargsDeserializer(Place),
            children=[
                StrField(
                    label="City",
                    extra_data_constraints=[FunctionConstraint(str.istitle)],
                ),
                StrField(label="Country"),
            ],
        ),
    )


def test_list_of_places_form_make_object(list_of_places_form):
    data = [
        {"city": "Los Gatos", "country": "USA"},
        {"city": "Los Angeles", "country": "USA"},
    ]
    obj = [Place(**kwargs) for kwargs in data]
    assert list_of_places_form.make_object(data) == obj

    with pytest.raises(FormErrors):
        list_of_places_form.make_object(data + [{"city": "sonoma", "country": "USA"}])


def test_list_of_places_form_serialize(list_of_places_form):
    data = [
        {"city": "Los Gatos", "country": "USA"},
        {"city": "Los Angeles", "country": "USA"},
    ]
    obj = [Place(**kwargs) for kwargs in data]
    assert list_of_places_form.serialize(obj) == data
