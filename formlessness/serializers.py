from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Callable, Generic, Protocol

from formlessness.types import D, JSONDict, T


class Serializer(ABC, Generic[T, D]):
    """
    Moves from the object stage to the data stage.

    todo: have serializers optionally return their json validators, IE type checks. In and/or out?
    """

    def serialize(self, obj: T) -> D:
        return obj


@dataclass
class FunctionSerializer(Serializer):
    function: Callable

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def serialize(self, obj: T) -> D:
        return self.function(obj)


def serializer(f):
    return FunctionSerializer(f)


class AsDict(Protocol):
    def as_dict(self) -> JSONDict:
        pass


@serializer
def as_dict(obj: AsDict) -> JSONDict:
    return obj.as_dict()
