from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic

from formlessness.exceptions import ValidationIssue
from formlessness.types import D, JSONDict, T

if TYPE_CHECKING:
    from formlessness.forms import Form


class Deserializer(ABC, Generic[T, D]):
    """
    Moves from the data stage to the object stage. Raise ValidationError if unable.
    """

    def deserialize(self, data: D) -> T:
        return data


@dataclass
class FunctionDeserializer(Deserializer, Generic[T, D]):
    function: Callable[[D], T]
    error_message: str

    def deserialize(self, data: D) -> T:
        try:
            return self.function(data)
        except (TypeError, ValueError, AttributeError) as e:
            raise ValidationIssue(self.error_message) from e


@dataclass
class KwargsDeserializer(FunctionDeserializer[T, D]):
    def deserialize(self, data: D) -> T:
        try:
            return self.function(**data)
        except (TypeError, ValueError, AttributeError) as e:
            raise ValidationIssue(self.error_message) from e


class FormDeserializer(Deserializer[T, D], ABC, Generic[T, D]):
    def deserialize(self, data: D, form: Form | None = None) -> T:
        return super().deserialize(data)


@dataclass
class BasicFormDeserializer(FormDeserializer[T, JSONDict]):
    def deserialize(self, data: D, form: Form = None) -> T:
        # todo: change to build up ValidationIssueMap on errors
        data = {
            child.key: child.deserialize(sub_data)
            for child, sub_data in form.converter_to_sub_data(data).items()
        }
        return super().deserialize(data)


@dataclass
class FormKwargsDeserializer(BasicFormDeserializer, KwargsDeserializer):
    pass


def deserializer(error_message: str):
    def f(constructor: Callable) -> FunctionDeserializer:
        return FunctionDeserializer(constructor, error_message)

    return f


class HasDeserializer(Deserializer[T, D], ABC, Generic[T, D]):
    deserializer: Deserializer

    def deserialize(self, data: D) -> T:
        return self.deserializer.deserialize(data)
