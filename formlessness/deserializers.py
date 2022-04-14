from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Generic

from formlessness.exceptions import ValidationIssue
from formlessness.types import D, T


class Deserializer(Generic[T, D], ABC):
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
class KwargsDeserializer(Deserializer[T, dict[str, Any]], Generic[T]):
    function: Callable[[...], T]
    error_message: str

    def deserialize(self, data: dict[str, Any]) -> T:
        try:
            return self.function(**data)
        except (TypeError, ValueError, AttributeError) as e:
            raise ValidationIssue(self.error_message) from e


def deserializer(error_message: str):
    def f(constructor: Callable) -> FunctionDeserializer:
        return FunctionDeserializer(constructor, error_message)

    return f
