from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Protocol

from formlessness.exceptions import ValidationIssue
from formlessness.forms import AbstractBasicForm
from formlessness.types import D, JSONDict, T


class Deserializer(Protocol[T, D]):
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


class FormDeserializer(Deserializer[T, JSONDict]):
    form: AbstractBasicForm

    def deserialize(self, data: JSONDict) -> T:
        """
        todo: change to build up ValidationIssueMap on errors
        """
        data = {
            child.key: child.deserialize(sub_data)
            for child, sub_data in self.form.converter_to_sub_data(data)
        }
        return super().deserialize(data)


@dataclass
class FormKwargsDeserializer(FormDeserializer, KwargsDeserializer):
    pass


def deserializer(error_message: str):
    def f(constructor: Callable) -> FunctionDeserializer:
        return FunctionDeserializer(constructor, error_message)

    return f


class HasDeserializer(Deserializer, Protocol):
    deserializer: Deserializer

    def deserialize(self, data: D) -> T:
        return self.deserializer.deserialize(data)
