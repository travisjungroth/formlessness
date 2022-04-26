from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Container, Final, Generic, Iterable, Mapping, Sequence

from formlessness.types import T


class Constraint(Generic[T], ABC):
    def validate(self, value: T) -> Constraint:
        return Valid if self.satisfied_by(value) else self

    def satisfied_by(self, value: T) -> bool:
        return bool(self.validate(value))

    def __bool__(self) -> bool:
        return False

    def __and__(self, other: Constraint) -> Constraint:
        return And([self, other])

    def __or__(self, other: Constraint) -> Constraint:
        return Or([self, other])

    def simplify(self) -> Constraint:
        return self


def constraint(message: str) -> Callable[[], FunctionConstraint]:
    """
    Decorator to make a Constraint from a function.
    """

    def f(function):
        return FunctionConstraint(function, message)

    return f


class ValidClass(Constraint[Any]):
    __singleton: ValidClass

    def __new__(cls):
        if not hasattr(cls, "__singleton"):
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def validate(self, value: Any) -> True:
        return self

    def satisfied_by(self, value: T) -> bool:
        return True

    def __bool__(self) -> bool:
        return True

    def __or__(self, other):
        return self

    def __and__(self, other):
        return other


Valid: Final[ValidClass] = ValidClass()


@dataclass
class Or(Constraint[T]):
    """
    Combine multiple Constraints, and one needs to pass.
    """

    constraints: Sequence[Constraint]

    def validate(self, value: T) -> Constraint:
        return Or([v.validate(value) for v in self.constraints]).simplify()

    def __str__(self):
        return "\nor\n".join(map(str, self.constraints))

    def __bool__(self):
        return any(self.constraints)

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
        return Or(constraints)


@dataclass
class And(Constraint[T]):
    """
    Combine multiple Constraints together that must pass.
    """

    constraints: Sequence[Constraint]

    def validate(self, value: T) -> Constraint:
        return And([v.validate(value) for v in self.constraints]).simplify()

    def __str__(self):
        return "\nand\n".join(map(str, self.constraints))

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
        return And(constraints)


@dataclass
class FunctionConstraint(Constraint[T]):
    """
    Pass in a predicate function that takes a value and returns True if valid.
    """

    function: Callable[[T], bool]
    message: str = ""

    def __post_init__(self):
        if not self.message:
            self.message = f"Must pass `{self.function.__qualname__}` constraint."

    def __call__(self, *args, **kwargs):
        # Preserve the function, should do wraps or something maybe
        return self.function(*args, **kwargs)

    def satisfied_by(self, value: T) -> bool:
        return self.function(value)

    def __str__(self):
        return self.message


@dataclass
class TypeConstraint(Constraint[T]):
    """
    Do an isinstance check against a type.
    """

    type_: type
    message: str

    def __post_init__(self):
        self.message = self.message.format(self.type_.__qualname__)

    def satisfied_by(self, value: T) -> bool:
        return isinstance(value, self.type_)

    def __str__(self):
        return self.message


@dataclass
class ChoicesConstraint(Constraint[T]):
    choices: Container
    message: str = "Must be a valid choice."

    def satisfied_by(self, value: T) -> bool:
        return value in self.choices

    def __str__(self):
        return self.message


@dataclass
class EachItem(Constraint[Iterable[T]]):
    item_constraint: Constraint[T]
    message: str = ""

    def __post_init__(self):
        if not isinstance(self.item_constraint, Constraint) and isinstance(
            self.item_constraint, Callable
        ):
            self.item_constraint = FunctionConstraint(self.item_constraint)
        if not self.message:
            self.message = f"Each item {str(self.item_constraint).lower()}."

    def satisfied_by(self, value: Iterable[T]) -> bool:
        return isinstance(value, Iterable) and all(
            self.item_constraint.validate(item) for item in value
        )

    def __str__(self):
        return self.message


is_int = TypeConstraint(int, "Must be an integer.")
is_str = TypeConstraint(str, "Must be a string.")
is_date = TypeConstraint(date, "Must be a date.")
is_list = TypeConstraint(list, "Must be a list.")
each_item_is_str = EachItem(is_str)


@constraint("Must not be set.")
def is_null(value: Any) -> bool:
    return value is None


class ConstraintMap(Mapping[tuple[str, ...], Constraint]):
    def __init__(
        self,
        top_constraint: Constraint = Valid,
        sub_maps: Mapping[str, ConstraintMap] = None,
    ) -> None:
        self.top_constraint = top_constraint
        self.sub_maps = sub_maps or {}

    def __getitem__(self, item: Sequence[str]) -> Constraint:
        if not item:
            return self.top_constraint
        try:
            return self.sub_maps[item[0]][item[1:]]
        except KeyError:
            return Valid

    def __iter__(self) -> Iterable[tuple[str, ...]]:
        if self.top_constraint is not Valid:
            yield ()
        for k1, sub_map in self.sub_maps.items():
            for k2 in sub_map:
                yield (k1,) + k2

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self):
        return all(self.values())

    def __and__(self, other):
        if not isinstance(other, ConstraintMap):
            raise NotImplementedError
        top_constraint = self.top_constraint & other.top_constraint
        sub_maps = self.sub_maps.copy()
        for k, v in other.sub_maps.items():
            if k in sub_maps:
                sub_maps[k] &= v
            else:
                sub_maps[k] = v
        return ConstraintMap(top_constraint, sub_maps)

    def __str__(self):
        return "\n".join([f"{'.'.join(k)}: {v}" for k, v in self.items()])
