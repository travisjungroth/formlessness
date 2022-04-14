from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, Protocol

from formlessness.types import D, JSONDict, T

if TYPE_CHECKING:
    from formlessness.forms import Form


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


class FormSerializer(Serializer[T, JSONDict], ABC, Generic[T]):
    form: Form

    def serialize(self, obj: T) -> JSONDict:
        d = {}
        for child, sub_obj in self.form.converter_to_sub_object(obj):
            d[child.key] = child.serialize(sub_obj)
        return super().serialize(d)


class AsDict(Protocol):
    def as_dict(self) -> JSONDict:
        pass


@serializer
def as_dict(obj: AsDict) -> JSONDict:
    return obj.as_dict()


class HasSerializer(Serializer[T, D], Generic[T, D]):
    serializer: Serializer

    def serialize(self, obj: T) -> D:
        return self.serializer.serialize(obj)
