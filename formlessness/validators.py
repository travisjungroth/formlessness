from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Container, Generic, Iterable, Mapping, Sequence

from formlessness.types import T


class Validator(Generic[T], ABC):
    """
    A validator takes a value and returns the issues.
    """

    @abstractmethod
    def validate(self, value: T) -> Validator:
        pass

    def __bool__(self) -> bool:
        return False

    def __and__(self, other: Validator) -> Validator:
        return And([self, other])

    def __or__(self, other: Validator) -> Validator:
        return Or([self, other])

    def simplify(self) -> Validator:
        return self


def validator(message: str) -> Callable[[], FunctionValidator]:
    """
    Decorator to make a Validators from a function.
    """

    def f(function):
        return FunctionValidator(function, message)

    return f


class ValidClass(Validator[Any]):
    def validate(self, value: Any) -> True:
        return self

    def __bool__(self) -> bool:
        return True

    def __or__(self, other):
        return self

    def __and__(self, other):
        return other


Valid = ValidClass()


@dataclass
class Or(Validator[T]):
    """
    Combine multiple Validators, and one needs to pass.
    """

    validators: Sequence[Validator]

    def validate(self, value: T) -> Validator:
        return Or([v.validate(value) for v in self.validators]).simplify()

    def __str__(self):
        return "\nor\n".join(map(str, self.validators))

    def __bool__(self):
        return any(self.validators)

    def simplify(self) -> Validator:
        if not self.validators:
            return Valid
        if len(self.validators) == 1:
            return self.validators[0].simplify()
        validators = []
        for v in self.validators:
            v = v.simplify()
            if v is Valid:
                return Valid
            if isinstance(v, Or):
                validators.extend(v.validators)
            else:
                validators.append(v)
        return Or(validators)


@dataclass
class And(Validator[T]):
    """
    Combine multiple Validators together that must pass.
    """

    validators: Sequence[Validator]

    def validate(self, value: T) -> Validator:
        return And([v.validate(value) for v in self.validators]).simplify()

    def __str__(self):
        return "\nand\n".join(map(str, self.validators))

    def __bool__(self):
        return all(self.validators)

    def simplify(self) -> Validator:
        validators = []
        for v in self.validators:
            v = v.simplify()
            if v is Valid:
                continue
            if isinstance(v, And):
                validators.extend(v.validators)
            else:
                validators.append(v)
        if not validators:
            return Valid
        if len(validators) == 1:
            return validators[0]
        return And(validators)


class PredicateValidator(Validator[T], ABC):
    """
    Implement the predicate method to return True if valid.
    """

    message: str

    @abstractmethod
    def predicate(self, value: T) -> bool:
        pass

    def validate(self, value: T) -> Validator:
        return Valid if self.predicate(value) else self

    def __str__(self) -> str:
        return self.message


@dataclass
class FunctionValidator(PredicateValidator[T]):
    """
    Pass in a predicate function that takes a value and returns True if valid.
    """

    function: Callable[[T], bool]
    message: str = ""

    def __post_init__(self):
        if not self.message:
            self.message = f"Must pass `{self.function.__qualname__}` validator."

    def __call__(self, *args, **kwargs):
        # Preserve the function, should do wraps or something maybe
        return self.function(*args, **kwargs)

    def predicate(self, value: T) -> bool:
        return self.function(value)


@dataclass
class TypeValidator(PredicateValidator[T]):
    """
    Do an isinstance check against a type.
    """

    type_: type
    message: str

    def __post_init__(self):
        self.message = self.message.format(self.type_.__qualname__)

    def predicate(self, value: T) -> bool:
        return isinstance(value, self.type_)


@dataclass
class ChoicesValidator(PredicateValidator[T]):
    choices: Container
    message: str = "Must be a valid choice."

    def predicate(self, value: T) -> bool:
        return value in self.choices


@dataclass
class EachItem(PredicateValidator[Iterable[T]]):
    item_validator: Validator[T]
    message: str = ""

    def __post_init__(self):
        if not isinstance(self.item_validator, Validator) and isinstance(
            self.item_validator, Callable
        ):
            self.item_validator = FunctionValidator(self.item_validator)
        if not self.message:
            self.message = f"Each item {str(self.item_validator).lower()}."

    def predicate(self, value: Iterable[T]) -> bool:
        return isinstance(value, Iterable) and all(
            self.item_validator.validate(item) for item in value
        )


is_int = TypeValidator(int, "Must be an integer.")
is_str = TypeValidator(str, "Must be a string.")
is_date = TypeValidator(date, "Must be a date.")
is_list = TypeValidator(list, "Must be a list.")
each_item_is_str = EachItem(is_str)


@validator("Must not be set.")
def is_null(value: Any) -> bool:
    return value is None


class ValidatorMap(Mapping[tuple[str, ...], Validator]):
    def __init__(
        self,
        top_validator: Validator = Valid,
        sub_maps: Mapping[str, ValidatorMap] = None,
    ) -> None:
        self.top_validator = top_validator
        self.sub_maps = sub_maps or {}

    def __getitem__(self, item: Sequence[str]) -> Validator:
        if not item:
            return self.top_validator
        try:
            return self.sub_maps[item[0]][item[1:]]
        except KeyError:
            return Valid

    def __iter__(self) -> Iterable[tuple[str, ...]]:
        if self.top_validator is not Valid:
            yield ()
        for k1, sub_map in self.sub_maps.items():
            for k2 in sub_map:
                yield (k1,) + k2

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self):
        return all(self.values())

    def __and__(self, other):
        if not isinstance(other, ValidatorMap):
            raise NotImplementedError
        top_validator = self.top_validator & other.top_validator
        sub_maps = self.sub_maps.copy()
        for k, v in other.sub_maps.items():
            if k in sub_maps:
                sub_maps[k] &= v
            else:
                sub_maps[k] = v
        return ValidatorMap(top_validator, sub_maps)

    def __str__(self):
        return "\n".join([f"{'.'.join(k)}: {v}" for k, v in self.items()])
