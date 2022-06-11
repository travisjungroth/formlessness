from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import time
from operator import ge
from operator import gt
from operator import le
from operator import lt
from typing import Any, Optional
from typing import Callable
from typing import ClassVar
from typing import Container
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Mapping
from typing import Sequence

from formlessness.types import T, JSONData, JSONDict

"""
Base class
"""


class Constraint(Generic[T], ABC):
    """
    Constraints are rules that can be satisfied by values.
    >>> is_int.satisfied_by(0)
    True

    Constraints can be made from other Constraints. These are complex, as opposed to simple.
    >>> Or(is_int, is_str).satisfied_by(0.5)
    False

    Validating a Constraint tells you what's unsatisfying about the value.
    >>> is_list_of_strings = is_list & EachItem(is_str)
    >>> str(is_list_of_strings.validate({'1', '2'}))
    'Must be a list.'

    Constraints that are satisfied by all values are truthy. Others are falsy.
    >>> bool(Or() and And() and Valid)
    True

    When implementing a Constraint class, one or both of satisfied_by() and validate() must be implemented.
    """

    # The Constraints that must always be checked before this Constraint is checked.
    # Use this to avoid duplicating checks, like type checks.
    requires: Iterable[Constraint] = ()

    def requirements_satisfied_by(self, value: T) -> bool:
        return all(x.satisfied_by(value) for x in self.requires)

    def satisfied_by(self, value: T) -> bool:
        """
        Returns True iff the value satisfies this Constraint.
        """
        return self.requirements_satisfied_by(value) and bool(self.validate(value))

    def validate(self, value: T) -> Constraint:
        """
        Returns the remaining Constraints that must be satisfied for this value to satisfy this Constraint.

        This method tells you what's "wrong" with the provided value. If the value satisfies the Constraint, this method
        will return a truthy Constraint. The default implementation will work for most simple Constraints, and will need
        to be replaced for complex Constraints.
        """
        return Valid if self.satisfied_by(value) else self

    def __bool__(self) -> bool:
        """
        Returns True iff this Constraint is always satisfied.
        """
        return False

    def __and__(self, other: Constraint) -> Constraint:
        return And(self, other)

    def __or__(self, other: Constraint) -> Constraint:
        return Or(self, other)

    def simplify(self) -> Constraint:
        """
        Returns a functionally identical but reduced Constraint.
        """
        return self

    @abstractmethod
    def __str__(self):
        pass

    def json_schema(self) -> JSONDict:
        return {}


"""
Simple Constraints
"""


class ValidClass(Constraint[Any]):
    """
    This is the canonical Constraint that is always satisfied. Equivalent to true, top, ⊤, unit, 1, etc.
    """

    __singleton: ValidClass

    def __new__(cls):
        if not hasattr(cls, "__singleton"):
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def validate(self, value: Any) -> True:
        return self

    def satisfied_by(self, value: Any) -> bool:
        return True

    def __bool__(self) -> bool:
        return True

    def __str__(self):
        return "Valid"


Valid: Final[ValidClass] = ValidClass()


@dataclass
class FunctionConstraint(Constraint[T]):
    """
    Pass in a predicate function that takes a value and returns True if satisfied.
    """

    function: Callable[[T], bool]
    message: str = ""
    requires: Iterable[Constraint] = ()

    def __post_init__(self):
        if not self.message:
            self.message = f"Must pass `{self.function.__qualname__}` constraint."

    def __call__(self, *args, **kwargs):
        # todo: preserve the function metadata, perhaps with functools.wraps.
        return self.function(*args, **kwargs)

    def satisfied_by(self, value: T) -> bool:
        return self.requirements_satisfied_by(value) and self.function(value)

    def __str__(self):
        return self.message


def constraint(
    message: str = "", requires: Iterable[Constraint] = ()
) -> Callable[[Callable[[T], bool]], FunctionConstraint[T]]:
    """
    Decorator to make a Constraint from a function.

    @constraint("Must be uppercase.", requires=[is_str])
    def is_uppercase(value: str) -> bool:
        return value.isupper()
    """

    def f(function: Callable[[T], bool]) -> FunctionConstraint[T]:
        return FunctionConstraint(function, message, requires)

    return f


@dataclass
class OfType(Constraint[T]):
    """
    Do an isinstance check against a type.
    """

    type_: type
    message: str
    json_type: Optional[str] = None
    _instances: ClassVar[dict[type, OfType]] = {}

    def __post_init__(self):
        self._instances[self.type_] = self

    @classmethod
    def get(cls, type_: type) -> OfType:
        try:
            return cls._instances[type_]
        except KeyError:
            return cls(type_, f"Must be of type {type_}.")

    def satisfied_by(self, value: T) -> bool:
        return isinstance(value, self.type_)

    def __str__(self):
        return self.message

    def json_schema(self) -> JSONData:
        return {'type': self.json_type} if self.json_type else {}


@dataclass
class Choices(Constraint[T]):
    choices: Container
    message: str = "Must be a valid choice."

    def satisfied_by(self, value: T) -> bool:
        return value in self.choices

    def __str__(self):
        return self.message


# TODO: Add Between. Use inclusive start and stop.


@dataclass
class Comparison(Constraint[T]):
    operand: T
    operator: ClassVar[Callable[[T, T], bool]]
    comparison_string: ClassVar[str]

    def satisfied_by(self, value: T) -> bool:
        try:
            return self.operator(value, self.operand)
        except (NotImplementedError, TypeError):
            return False

    def __str__(self):
        return f"Must be {self.comparison_string} {self.operand}."


@dataclass
class GT(Comparison[T]):
    """
    Greater Than

    >>> GT(5).satisfied_by(6)
    True
    >>> GT('B').satisfied_by('A')
    False
    >>> GT(0).satisfied_by('1')
    False
    """

    operator: Callable[[T, T], bool] = gt
    comparison_string: str = "greater than"


@dataclass
class GE(Comparison[T]):
    """
    Greater Than Or Equal To
    """

    operator: Callable[[T, T], bool] = ge
    comparison_string: str = "greater than or equal to"


@dataclass
class LT(Comparison[T]):
    """
    Less Than
    """

    operator: Callable[[T, T], bool] = lt
    comparison_string: str = "less than"


@dataclass
class LE(Comparison[T]):
    """
    Less Than Or Equal To
    """

    operator: Callable[[T, T], bool] = le
    comparison_string: str = "less than or equal to"


# TODO: Add Not Equal (NEQ)
# TODO: Add Regexp

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

    def __init__(self, *constraints, message: str = ""):
        self.constraints: Sequence[Constraint] = constraints
        self.message = message

    def validate(self, value: T) -> Constraint:
        return Or(*[v.validate(value) for v in self.constraints]).simplify()

    def __str__(self):
        return self.message or "\nor\n".join(map(str, self.constraints))

    def __bool__(self):
        return not self.constraints or any(self.constraints)

    def simplify(self) -> Constraint:
        if not self.constraints:
            return Valid
        if len(self.constraints) == 1:
            return self.constraints[0].simplify()
        constraints = []
        for v in self.constraints:
            v = v.simplify()
            if v is Valid:
                return Valid
            if isinstance(v, Or):
                constraints.extend(v.constraints)
            else:
                constraints.append(v)
        return Or(*constraints)


@dataclass
class And(Constraint[T]):
    """
    Combine multiple Constraints, and all must be satisfied.
    """

    constraints: Sequence[Constraint]
    message: str = ""

    def __init__(self, *constraints, message: str = ""):
        self.constraints: Sequence[Constraint] = constraints
        self.message = message

    def validate(self, value: T) -> Constraint:
        return And(*[v.validate(value) for v in self.constraints]).simplify()

    def __str__(self):
        return self.message or "\nand\n".join(map(str, self.constraints))

    def __bool__(self):
        return all(self.constraints)

    def simplify(self) -> Constraint:
        constraints = []
        for v in self.constraints:
            v = v.simplify()
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
        return And(*constraints)


# TODO: Add Not
# TODO: Add Implies, maybe called If or Conditional https://en.wikipedia.org/wiki/Material_conditional


@dataclass
class EachItem(Constraint[Iterable[T]]):
    """
    Check a Constraint against all items of an Iterable.
    """

    item_constraint: Constraint[T]
    message: str = ""

    def __post_init__(self):
        if not self.message:
            self.message = f"Each item {str(self.item_constraint).lower()}."
        self.requires = [is_iterable]

    def satisfied_by(self, value: Iterable[T]) -> bool:
        return self.requirements_satisfied_by(value) and all(
            self.item_constraint.validate(item) for item in value
        )

    def __str__(self):
        return self.message


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
        return "\n".join([f"{'.'.join(k)}: {v}" for k, v in self.items()])


"""
Constraint instances
"""


is_int = OfType(int, "Must be an integer.", 'integer')
is_float = OfType(float, "Must be a float.", 'number')
is_str = OfType(str, "Must be a string.", 'string')
is_date = OfType(date, "Must be a date.")
is_datetime = OfType(datetime, "Must be a datetime.")
is_time = OfType(time, "Must be a time.")
is_list = OfType(list, "Must be a list.", "array")
is_dict = OfType(dict, "Must be a dictionary.", 'object')
is_null = OfType(type(None), "Must not be set.", "null")
is_bool = OfType(bool, "Must be a boolean.", "boolean")
is_iterable = OfType(Iterable, "Must be iterable.")
is_list_of_str = list_of(is_str, "Must be a list of strings.")
is_list_of_int = list_of(is_int, "Must be a list of integers.")
