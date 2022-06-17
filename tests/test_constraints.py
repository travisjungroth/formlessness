from formlessness.constraints import GE, constraint_to_json, to_json, Comparison


def test_json_ge():
    assert to_json(GE(100)) == ({"minimum": 100}, True)


def test_json_ge_non_number():
    assert to_json(GE("A")) == ({}, False)


def test_json_comparison_unsupported():
    constraint = Comparison(100)
    constraint.operator = lambda x: True
    assert to_json(constraint) == ({}, False)
