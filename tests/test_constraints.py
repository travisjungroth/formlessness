from formlessness.constraints import GE
from formlessness.constraints import Comparison
from formlessness.constraints import Regex
from formlessness.constraints import to_json


def test_regex():
    constraint = Regex(r"\w+")
    assert constraint.satisfied_by("snake_case")
    assert not constraint.satisfied_by("abc!")
    assert str(constraint) == r"Must match regex \w+"
    assert not Regex(r"\w").satisfied_by("snake_case")


def test_json_ge():
    assert to_json(GE(100)) == ({"minimum": 100}, True)


def test_json_ge_non_number():
    assert to_json(GE("A")) == ({}, False)


def test_json_comparison_unsupported():
    constraint = Comparison(100)
    constraint.operator = lambda x: True
    assert to_json(constraint) == ({}, False)
