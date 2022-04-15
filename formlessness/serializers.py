from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Callable, Generic, Protocol

from formlessness.types import D, JSONDict, T


class Serializer(Generic[D, T], ABC):
    """
    Moves from the object stage to the data stage.
    """

    def serialize(self, obj: T) -> D:
        return obj


def serializer(f: Callable[[T], D]) -> FunctionSerializer[D, T]:
    """
    Decorator to turn a function into a Serializer.
    """
    return FunctionSerializer(f)


@dataclass
class FunctionSerializer(Serializer[D, T]):
    function: Callable[[T], D]

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def serialize(self, obj: T) -> D:
        return self.function(obj)


class AsDict(Protocol):
    def as_dict(self) -> JSONDict:
        pass


@serializer
def as_dict(obj: AsDict) -> JSONDict:
    return obj.as_dict()
