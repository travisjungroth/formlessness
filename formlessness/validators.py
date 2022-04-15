from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Container, Generic, Iterable, Sequence

from formlessness.exceptions import ValidationIssue
from formlessness.types import T


class Validator(Generic[T], ABC):
    """
    A validator takes a value and returns the issues.
    """

    def validate(self, value: T) -> Sequence[ValidationIssue]:
        return []


def validator(message: str) -> Callable[[], FunctionValidator]:
    """
    Decorator to make a Validators from a function.
    """

    def f(function):
        return FunctionValidator(function, message)

    return f


@dataclass
class Or(Validator[T]):
    """
    Combine multiple Validators, and one needs to pass.
    """

    validators: Sequence[Validator]

    def validate(self, value: T) -> Sequence[ValidationIssue]:
        issue_groups = [v.validate(value) for v in self.validators]
        if not all(issue_groups):
            return ()
        message_groups = []
        for issues in issue_groups:
            message_groups.append("\n".join(map(str, issues)))
        # todo: this could be handled better. It inherently needs to be a tree, not strings.
        message = "\nor\n".join(message_groups)
        return [ValidationIssue(message)]


@dataclass
class And(Validator[T]):
    """
    Combine multiple Validators together that must pass.
    """

    validators: Sequence[Validator]

    def validate(self, value: T) -> Sequence[ValidationIssue]:
        return [issue for v in self.validators for issue in v.validate(value)]


class PredicateValidator(Validator[T], ABC):
    """
    Implement the predicate method to return True if valid.
    """

    message: str

    @abstractmethod
    def predicate(self, value: T) -> bool:
        pass

    def validate(self, value: T) -> Sequence[ValidationIssue]:
        return () if self.predicate(value) else (ValidationIssue(str(self)),)

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
        return isinstance(value, Iterable) and not any(
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
