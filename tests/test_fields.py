import pytest

from formlessness.exceptions import ValidationIssue, ValidationIssueMap
from formlessness.fields import CommaListStrField, IntField


class TestCommaListStrField:
    @pytest.fixture(scope="session")
    def field(self):
        return CommaListStrField("Label")

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
        assert not field.data_issues(good_data)

    def test_has_data_issues(self, field, bad_data: str):
        assert field.data_issues(bad_data)

    def test_no_object_issues(self, field, good_obj):
        assert not field.object_issues(good_obj)

    def test_has_object_issues(self, field, bad_obj: list[str]):
        assert field.object_issues(bad_obj)

    def test_deserialize(self, field, good_data, good_obj):
        assert field.deserialize(good_data) == good_obj

    def test_deserialize_error(self, field, bad_data):
        with pytest.raises(ValidationIssue):
            field.deserialize(bad_data)  # noqa

    def test_make_object(self, field, good_data, good_obj):
        assert field.make_object(good_data) == good_obj

    def test_make_object_error(self, field, bad_data: str):
        with pytest.raises(ValidationIssueMap):
            field.make_object(bad_data)


def test_serialize():
    field = CommaListStrField("Label")
    assert field.serialize(["A", "B"]) == "A,B"


def test_choices():
    field = IntField("Label", choices=[1, 2, 3])
    assert not field.data_issues(1)
    assert field.data_issues(4)
    assert field.data_issues("A")
    assert field.data_issues(None)
