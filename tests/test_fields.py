from datetime import date

import pytest

from formlessness.exceptions import DeserializationError, FormErrors
from formlessness.fields import CommaListStrField, IntField, seperated_field, DateTimeField


class TestCommaListStrField:
    @pytest.fixture(
        scope="session",
        params=[CommaListStrField("Label"), seperated_field(",", label="Label")],
    )
    def field(self, request):
        return request.param

    @pytest.fixture(params=[1, None, (), {}])
    def bad_data(self, request):
        return request.param

    @pytest.fixture(params=["a,b,c", (), {}, 1, None, ["A", 1]])
    def bad_obj(self, request):
        return request.param

    @pytest.fixture(
        params=[
            ("", []),
            (",", []),
            ("A,", ["A"]),
            (",A", ["A"]),
            ("A,B", ["A", "B"]),
            ("1,B", ["1", "B"]),
            ("1,1.0,A,,,..", ["1", "1.0", "A", ".."]),
        ]
    )
    def data_to_object(self, request):
        return request.param

    @pytest.fixture
    def good_data(self, data_to_object):
        data, obj = data_to_object
        return data

    @pytest.fixture
    def good_obj(self, data_to_object):
        data, obj = data_to_object
        return obj

    def test_no_data_issues(self, field, good_data):
        assert field.validate_data(good_data)

    def test_has_data_issues(self, field, bad_data: str):
        assert not field.validate_data(bad_data)

    def test_no_object_issues(self, field, good_obj):
        assert field.validate_object(good_obj)

    def test_has_object_issues(self, field, bad_obj: list[str]):
        assert not field.validate_object(bad_obj)

    def test_deserialize(self, field, good_data, good_obj):
        assert field.deserialize(good_data) == good_obj

    def test_deserialize_error(self, field, bad_data):
        with pytest.raises(DeserializationError):
            field.deserialize(bad_data)  # noqa

    def test_make_object(self, field, good_data, good_obj):
        assert field.make_object(good_data) == good_obj

    def test_make_object_error(self, field, bad_data: str):
        with pytest.raises(FormErrors):
            field.make_object(bad_data)


def test_serialize():
    field = CommaListStrField("Label")
    assert field.serialize(["A", "B"]) == "A,B"


def test_choices():
    field = IntField("Label", choices=[1, 2, 3])
    assert field.validate_data(1)
    assert not field.validate_data(4)
    assert not field.validate_data("A")  # noqa
    assert not field.validate_data(None)  # noqa

    field = DateTimeField("Label")
    assert field.validate_data("2022-05-18T09:50:40.787030")
    assert not field.validate_object(date.today())
