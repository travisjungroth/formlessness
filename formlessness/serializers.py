from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable
from typing import Generic
from typing import Iterable
from typing import Protocol
from typing import cast

from formlessness.types import D
from formlessness.types import JSONDict
from formlessness.types import T


class Serializer(Generic[D, T], ABC):
    """
    Moves from the object stage to the data stage.
    """

    def serialize(self, obj: T) -> D:
        return cast(D, obj)


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


@dataclass
class JoinSerializer(Serializer[str, Iterable]):
    separator: str

    def serialize(self, obj: Iterable) -> str:
        return self.separator.join(map(str, obj))


@dataclass
class MethodSerializer(Serializer[D, T]):
    method_name: str

    def serialize(self, obj: T) -> D:
        method = getattr(obj, self.method_name)
        return method()


class AsDict(Protocol):
    @abstractmethod
    def as_dict(self) -> JSONDict:
        pass


as_dict: MethodSerializer[JSONDict, AsDict] = MethodSerializer("as_dict")


class ISOFormat(Protocol):
    @abstractmethod
    def isoformat(self) -> str:
        pass


isoformat: MethodSerializer[str, ISOFormat] = MethodSerializer("isoformat")
