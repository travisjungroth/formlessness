from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import replace
from datetime import date
from datetime import datetime
from datetime import time
from functools import singledispatch
from operator import ge
from operator import gt
from operator import le
from operator import lt
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Container
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Mapping
from typing import Sequence

from formlessness.types import JSONDict
from formlessness.types import T

"""
Base class
"""


class Constraint(Generic[T], ABC):
    """
    Constraints are rules that can be satisfied by values.
    >>> is_int.satisfied_by(0)
    True

    Constraints can be made from other Constraints.
    These are called complex, as opposed to simple.
    >>> Or(is_int, is_str).satisfied_by('A')
    True

    Validating a Constraint returns the unsatisfied Constraints.
    >>> is_positive_int = is_int & GT(0)
    >>> is_positive_int.validate(-1)
    GT(0)

    Casting a constraint as a string should give a human-readable message.
    >>> str(EachItem(is_str))
    'Each item must be a string.'

    Constraints that are satisfied by all values are truthy. Others are falsy.
    Combine this with .validate() to see what, if anything, is unsatisfied.
    >>> valid = (GT(0) & LT(10)).validate(20)
    >>> if not valid:
    ...    str(valid)
    'Must be less than 10.'

    When implementing a Constraint class, one or both of satisfied_by() and validate()
    must be reimplemented.
    """

    def satisfied_by(self, value: T) -> bool:
        """
        Returns True iff the value satisfies this Constraint.
        """
        return bool(self.validate(value))

    def validate(self, value: T) -> Constraint:
        """
        Returns the remaining Constraints that must be satisfied for this value to satisfy this Constraint.

        This method tells you what's "wrong" with the provided value. If the value satisfies the Constraint, this method
        will return a truthy Constraint. The default implementation will work for most simple Constraints, and will need
        to be replaced for complex Constraints.
        """
        return Valid if self.satisfied_by(value) else self.simplify()

    def __bool__(self) -> bool:
        """
        Returns True iff this Constraint is always satisfied.
        >>> bool(Valid) and bool(And())
        True
        >>> bool(GT(0))
        False
        """
        return self.simplify() is Valid

    def __and__(self, other: Constraint) -> Constraint:
        """
        >>> float_over_10 = is_float & GT(10)
        >>> float_over_10.satisfied_by(11)
        False
        """
        return And(self, other)

    def __or__(self, other: Constraint) -> Constraint:
        """
        >>> big_or_small = LT(10) | GT(1000)
        >>> big_or_small.satisfied_by(5)
        True
        """
        return Or(self, other)

    def __invert__(self) -> Constraint:
        """
        >>> not_list = ~is_list
        >>> not_list.satisfied_by(1)
        True
        """
        return Not(self)

    def simplify(self) -> Constraint:
        """
        Returns a functionally identical but reduced Constraint.
        """
        return self

    @abstractmethod
    def __str__(self):
        """
        Should provide a human readable message.
        """


"""
Simple Constraints
"""


class ValidClass(Constraint[Any]):
    """
    This is the canonical Constraint that is always satisfied.
    Equivalent to true, top, ⊤, 1, etc.

    Use its singleton Valid, just like how None is a singleton.
    """

    __singleton: ValidClass

    def __new__(cls):
        if not hasattr(cls, "__singleton"):
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def validate(self, value: Any) -> ValidClass:
        return self

    def satisfied_by(self, value: Any) -> bool:
        return True

    def __bool__(self) -> bool:
        return True

    def __invert__(self) -> InvalidClass:
        return Invalid

    def __repr__(self):
        return "Valid"

    def __str__(self) -> str:
        return "Valid"


Valid: Final[ValidClass] = ValidClass()


class InvalidClass(Constraint[Any]):
    """
    This is the canonical Constraint that is never satisfied.
    Equivalent to false, bottom, ⊥, 0, etc.

    Use its singleton Invalid, just like how None is a singleton.
    """

    __singleton: InvalidClass

    def __new__(cls):
        if not hasattr(cls, "__singleton"):
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def validate(self, value: Any) -> InvalidClass:
        return self

    def satisfied_by(self, value: Any) -> bool:
        return False

    def __invert__(self) -> ValidClass:
        return Valid

    def __repr__(self):
        return "Invalid"

    def __str__(self):
        return "Invalid"


Invalid: Final[InvalidClass] = InvalidClass()


@dataclass
class FunctionConstraint(Constraint[T]):
    """
    Pass in a predicate function that takes a value and returns True iff satisfied.
    """

    function: Callable[[T], bool]
    message: str = ""
    requires: Iterable[Constraint] = ()

    def __post_init__(self):
        if not self.message:
            self.message = f"Must pass `{self.function.__qualname__}` constraint."

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def satisfied_by(self, value: T) -> bool:
        return And(*self.requires).satisfied_by(value) and self.function(value)

    def __str__(self):
        return self.message


def constraint(
    message: str = "", requires: Iterable[Constraint] = ()
) -> Callable[[Callable[[T], bool]], FunctionConstraint[T]]:
    """
    Decorator to make a Constraint from a function.

    >>> @constraint("Must be uppercase.", requires=[is_str])
    ... def is_uppercase(value: str) -> bool:
    ...    return value.isupper()
    >>> is_uppercase.satisfied_by('ABC')
    True
    """

    def f(function: Callable[[T], bool]) -> FunctionConstraint[T]:
        return FunctionConstraint(function, message, requires)

    return f


@dataclass
class OfType(Constraint[T]):
    """
    Do an isinstance check against a type.

    >>> OfType(frozenset).satisfied_by(frozenset())
    True
    """

    type_: type
    message: str = "Must be of type {}."
    _instances: ClassVar[dict[type, OfType]] = {}

    @classmethod
    def get(
        cls,
        type_: type,
        message: str = "Must be of type {}.",
    ) -> OfType:
        """
        Dynamically get-or-create the Constraint for a type.
        Many are already declared in this file.
        >>> int_check = OfType.get(int)
        >>> int_check == is_int
        True
        >>> print(int_check)
        Must be an integer.
        """
        try:
            return cls._instances[type_]
        except KeyError:
            return cls(type_, message)

    def __post_init__(self):
        self._instances[self.type_] = self

    def satisfied_by(self, value: T) -> bool:
        return isinstance(value, self.type_)

    def __str__(self) -> str:
        return self.message.format(self.type_)


@dataclass
class Choices(Constraint[T]):
    choices: Container
    message: str = "Must be a valid choice."

    def satisfied_by(self, value: T) -> bool:
        return value in self.choices

    def __str__(self):
        return self.message


@dataclass
class Comparison(Constraint[T]):
    operand: T
    operator: ClassVar[Callable]

    def satisfied_by(self, value: T) -> bool:
        try:
            return self.operator(value, self.operand)
        except (NotImplementedError, TypeError):
            return False

    def __str__(self):
        docstring = self.__class__.__doc__
        if not docstring:
            raise Exception("Missing docstring for Comparison.")
        words = docstring.splitlines()[1].lower().strip()
        return f"Must be {words} {self.operand}."

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.operand})"


@dataclass(repr=False)
class GT(Comparison[T]):
    """
    Greater Than

    >>> GT(5).satisfied_by(6)
    True
    >>> GT(6).satisfied_by(5)
    False
    >>> GT('A').satisfied_by('B')
    True
    >>> GT(0).satisfied_by('1')
    False
    >>> print(GT(0))
    Must be greater than 0.
    >>> print(~GT(0))
    Must be less than or equal to 0.
    """

    operator: ClassVar[Callable] = gt

    def __invert__(self) -> LE:
        return LE(self.operand)


@dataclass(repr=False)
class GE(Comparison[T]):
    """
    Greater Than Or Equal To
    """

    operator: ClassVar[Callable] = ge

    def __invert__(self) -> LT:
        return LT(self.operand)


@dataclass(repr=False)
class LT(Comparison[T]):
    """
    Less Than
    """

    operator: ClassVar[Callable] = lt

    def __invert__(self) -> GE:
        return GE(self.operand)


@dataclass(repr=False)
class LE(Comparison[T]):
    """
    Less Than Or Equal To
    """

    operator: ClassVar[Callable] = le

    def __invert__(self) -> GT:
        return GT(self.operand)


@dataclass
class Regex(Constraint[str]):
    pattern: re.Pattern
    message: str = ""

    def __init__(self, pattern: str, message: str = ""):
        self.pattern: re.Pattern = re.compile(pattern)
        self.message = message

    def satisfied_by(self, value: str) -> bool:
        r"""
        >>> Regex("\w+").satisfied_by("snake_case")
        True
        >>> Regex("\w").satisfied_by("snake_case")
        False
        >>> Regex("\w+").satisfied_by("abc!")
        False
        """
        return self.pattern.fullmatch(value) is not None

    def __str__(self) -> str:
        r"""
        >>> print(Regex("\w+"))
        Must match regex \w+
        """
        return self.message or f"Must match regex {self.pattern.pattern}"


"""
Complex Constraints
"""


@dataclass
class Or(Constraint[T]):
    """
    Combine multiple Constraints, and one must be satisfied.
    """

    constraints: Sequence[Constraint]
    message: str = ""
    simplified: bool = False

    def __init__(self, *constraints, message: str = "", simplified: bool = False):
        self.constraints: Sequence[Constraint] = constraints
        self.message = message
        self.simplified = simplified

    def validate(self, value: T) -> Constraint:
        return Or(*[v.validate(value) for v in self.constraints]).simplify()

    def __str__(self):
        sep = "\nor\n"
        return self.message or f"({sep.join(map(str, self.constraints))})"

    def __bool__(self):
        return any(self.constraints)

    def __invert__(self) -> Constraint:
        return And(*[~c for c in self.constraints])

    def simplify(self) -> Constraint:
        """
        >>> Or(Invalid, Valid, Valid).simplify()
        Valid
        >>> Or(GT(1), Invalid).simplify()
        GT(1)
        >>> Or().simplify()
        Invalid
        """
        if self.simplified:
            return self
        constraints = []
        for v in self.constraints:
            v = v.simplify()
            if v is Valid:
                return Valid
            if v is Invalid:
                continue
            if isinstance(v, Or):
                constraints.extend(v.constraints)
            else:
                constraints.append(v)
        if not constraints:
            return Invalid
        if len(constraints) == 1:
            return constraints[0]
        return Or(*constraints, simplified=True)


@dataclass
class And(Constraint[T]):
    """
    Combine multiple Constraints, and all must be satisfied.
    """

    constraints: Sequence[Constraint]
    message: str = ""
    simplified: bool = False

    def __init__(self, *constraints, message: str = "", simplified: bool = False):
        self.constraints: Sequence[Constraint] = constraints
        self.message = message
        self.simplified = simplified

    def validate(self, value: T) -> Constraint:
        return And(*[v.validate(value) for v in self.constraints]).simplify()

    def __str__(self):
        sep = "\nand\n"
        return self.message or f"({sep.join(map(str, self.constraints))})"

    def __bool__(self):
        return all(self.constraints)

    def __invert__(self) -> Constraint:
        return Or(*[~c for c in self.constraints])

    def simplify(self) -> Constraint:
        """
        >>> And(Invalid, Valid, Valid).simplify()
        Invalid
        >>> And(GT(1), Valid).simplify()
        GT(1)
        >>> And().simplify()
        Valid
        """
        if self.simplified:
            return self
        constraints = []
        for v in self.constraints:
            v = v.simplify()
            if v is Invalid:
                return Invalid
            if v is Valid:
                continue
            if isinstance(v, And):
                constraints.extend(v.constraints)
            else:
                constraints.append(v)
        if not constraints:
            return Valid
        if len(constraints) == 1:
            return constraints[0]
        return And(*constraints, simplified=True)


@dataclass
class Not(Constraint[T]):
    constraint: Constraint
    message: str = ""
    simplified: bool = False

    def satisfied_by(self, value: T) -> bool:
        """
        >>> Not(is_str).satisfied_by(1)
        True
        >>> Not(is_str).satisfied_by('A')
        False
        """
        return not self.constraint.satisfied_by(value)

    def __str__(self):
        return self.message or f"Not ({self.constraint})"

    def __invert__(self) -> Constraint:
        return self.constraint

    def simplify(self) -> Constraint:
        """
        >>> Not(Valid).simplify()
        Invalid
        >>> str(Not(Not(is_str)).simplify())
        'Must be a string.'
        >>> Not(Not(And())).simplify()
        Valid
        >>> str(Not(is_str).simplify().simplify())
        'Not (Must be a string.)'
        """
        if self.simplified:
            return self
        inverted_constraint = ~self.constraint
        if isinstance(inverted_constraint, Not):
            return replace(self, constraint=self.constraint.simplify(), simplified=True)
        return inverted_constraint.simplify()


@dataclass
class If(Constraint[T]):
    p: Constraint
    q: Constraint
    message: str = ""

    def satisfied_by(self, value: T) -> bool:
        """
        >>> ints_are_positive = If(is_int, GT(0))
        >>> ints_are_positive.satisfied_by(-1)
        False
        >>> ints_are_positive.satisfied_by(1)
        True
        >>> ints_are_positive.satisfied_by('A')
        True
        >>> ints_are_positive.satisfied_by(-.5)
        True
        """
        if self.p.satisfied_by(value):
            return self.q.satisfied_by(value)
        return True

    def __str__(self) -> str:
        return self.message or f"If ({self.p}) Then ({self.q})"

    def simplify(self) -> Constraint:
        return Or(~self.p, self.q).simplify()


@dataclass
class EachItem(Constraint[Iterable]):
    """
    Check a Constraint against all items of an Iterable.
    """

    item_constraint: Constraint
    message: str = "Each item {}"

    def satisfied_by(self, value: Iterable) -> bool:
        """
        >>> EachItem(is_str).satisfied_by(['A'])
        True
        >>> EachItem(is_str).satisfied_by([1])
        False
        >>> EachItem(is_int).satisfied_by(1)
        False
        """
        try:
            return all(self.item_constraint.satisfied_by(item) for item in value)
        except TypeError:
            return False

    def __str__(self):
        """
        >>> print(EachItem(GT(0)))
        Each item must be greater than 0.
        """
        return self.message.format(str(self.item_constraint).lower())

    def simplify(self) -> Constraint:
        return Valid if self.item_constraint else self


def list_of(constraint: Constraint, message: str) -> Constraint:
    return And(is_list, EachItem(constraint), message=message)


"""
Constraint Collections
"""


class ConstraintMap(Mapping[tuple[str, ...], Constraint]):
    """
    This is meant to be used alongside Forms.
    The key is a path to the Form or Field. The value is the corresponding Constraint.
    defaults to Valid on missing keys.

    >>> field_constraint_map = ConstraintMap(is_int)
    >>> form_constraint_map = ConstraintMap(is_dict, {'field_key': field_constraint_map})
    >>> str(form_constraint_map[('field_key',)])
    'Must be an integer.'
    >>> str(form_constraint_map[()])
    'Must be a dictionary.'
    >>> str(form_constraint_map[('field_key', 'additional_key')])
    'Valid'
    """

    def __init__(
        self,
        top_constraint: Constraint = Valid,
        child_constraints: Mapping[str, ConstraintMap] = None,
    ) -> None:
        self._top_constraint = top_constraint
        self._sub_maps = child_constraints or {}

    def __getitem__(self, item: Sequence[str]) -> Constraint:
        if not item:
            return self._top_constraint
        try:
            return self._sub_maps[item[0]][item[1:]]
        except KeyError:
            return Valid

    def __iter__(self) -> Iterable[tuple[str, ...]]:
        if self._top_constraint is not Valid:
            yield ()
        for k1, sub_map in self._sub_maps.items():
            for k2 in sub_map:
                yield (k1,) + k2

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self):
        """This follows the __bool__ logic of Constraints. Return True iff all Constraints are always satisfied."""
        return all(self.values())

    def __and__(self, other: ConstraintMap) -> ConstraintMap:
        """
        Like a dict union, but values in both are combined with & instead of replaced.
        """
        if not isinstance(other, ConstraintMap):
            raise NotImplementedError
        top_constraint = self._top_constraint & other._top_constraint
        sub_maps = self._sub_maps.copy()
        for k, v in other._sub_maps.items():
            if k in sub_maps:
                sub_maps[k] &= v
            else:
                sub_maps[k] = v
        return ConstraintMap(top_constraint, sub_maps)

    def __str__(self):
        return "\n\n".join([f"{'.'.join(k)}: {v}" for k, v in self.items()])


"""
Constraint instances
"""

is_null = OfType(type(None), "Must not be set.")
is_int = OfType(int, "Must be an integer.")
is_float = OfType(float, "Must be a float.")
is_str = OfType(str, "Must be a string.")
is_bool = OfType(bool, "Must be a boolean.")
is_list = OfType(list, "Must be a list.")
is_dict = OfType(dict, "Must be a dictionary.")
is_datetime = OfType(datetime, "Must be a datetime.")
is_date = OfType(date, "Must be a date.")
is_time = OfType(time, "Must be a time.")
is_iterable = OfType(Iterable, "Must be iterable.")
is_list_of_str = list_of(is_str, "Must be a list of strings.")
is_list_of_int = list_of(is_int, "Must be a list of integers.")


@constraint("Must be set.")
def not_null(value: Any) -> bool:
    return value is not None


@dataclass
class HasKeys(Constraint[dict]):
    keys: list[str]

    def validate(self, value: dict) -> Constraint:
        missing_keys = [k for k in self.keys if k not in value]
        if not missing_keys:
            return Valid
        return HasKeys(missing_keys)

    def __str__(self):
        return f"Must set {', '.join(self.keys)}."


def constraint_to_json(constraint: Constraint) -> JSONDict:
    return to_json(constraint)[0]


@singledispatch
def to_json(constraint: Any) -> tuple[JSONDict, bool]:
    raise NotImplementedError()


@to_json.register
def _(constraint: Constraint) -> tuple[JSONDict, bool]:
    return {}, False


@to_json.register
def _(constraint: ValidClass) -> tuple[JSONDict, bool]:
    return {}, True


@to_json.register
def _(constraint: InvalidClass) -> tuple[JSONDict, bool]:
    return {"not": {}}, True


_python_type_to_json_type = {
    type(None): "null",
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
}


@to_json.register
def _(constraint: OfType) -> tuple[JSONDict, bool]:
    try:
        return {"type": _python_type_to_json_type[constraint.type_]}, True
    except KeyError:
        return {}, False


@to_json.register
def _(constraint: Or) -> tuple[JSONDict, bool]:
    validators = []
    for c in constraint.constraints:
        validator, faithful = to_json(c)
        if not faithful:
            return {}, False
        validators.append(validator)
    return {"anyOf": validators}, True


@to_json.register
def _(constraint: And) -> tuple[JSONDict, bool]:
    validators = []
    faithful = True
    for c in constraint.constraints:
        validator, faithful = to_json(c)
        if not faithful:
            faithful = False
        elif validator != {}:
            validators.append(validator)
    if not validators:
        return {}, faithful
    if len(validators) == 1:
        return validators[0], faithful
    return {"allOf": validators}, faithful


@to_json.register
def _(constraint: Not) -> tuple[JSONDict, bool]:
    validator, faithful = to_json(constraint.constraint)
    if faithful:
        return {"not": validator}, True
    return {}, False


@to_json.register
def _(constraint: Comparison) -> tuple[JSONDict, bool]:
    value = constraint.operand
    if not isinstance(value, float) and not isinstance(value, int):
        return {}, False
    d = {ge: "minimum", gt: "exclusiveMinimum", le: "maximum", lt: "exclusiveMaximum"}
    try:
        key = d[constraint.operator]
    except KeyError:
        return {}, False
    return {key: value}, True
