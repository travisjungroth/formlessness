from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Generic

from formlessness.types import D, T


class Deserializer(Generic[D, T], ABC):
    """
    Moves from the data stage to the object stage. Raise ValidationIssue if unable.
    """

    def deserialize(self, data: D) -> T:
        return data


def deserializer(error_message: str):
    """
    Decorator to turn a function into a deserializer.
    """

    def f(function: Callable[[D], T]) -> FunctionDeserializer[D, T]:
        return FunctionDeserializer(function, error_message)

    return f


class SerializationError(Exception):
    pass


@dataclass
class FunctionDeserializer(Deserializer[D, T]):
    function: Callable[[D], T]
    error_message: str

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def deserialize(self, data: D) -> T:
        try:
            return self.function(data)
        except (TypeError, ValueError, AttributeError) as e:
            raise SerializationError(self.error_message) from e


@dataclass
class KwargsDeserializer(Deserializer[dict[str, Any], T]):
    function: Callable[[...], T]
    error_message: str

    def deserialize(self, data: dict[str, Any]) -> T:
        try:
            return self.function(**data)
        except (TypeError, ValueError, AttributeError) as e:
            raise SerializationError(self.error_message) from e
