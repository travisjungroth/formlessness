"""
Base classes that didn't seem to need their own module.
"""
from __future__ import annotations

from abc import ABC
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Iterator,
    Mapping,
    Protocol,
    Sequence,
    Union,
)

from formlessness.deserializers import Deserializer
from formlessness.displayers import Displayer
from formlessness.exceptions import ValidationIssueMap
from formlessness.serializers import Serializer
from formlessness.types import D, JSONData, JSONDict, T

if TYPE_CHECKING:
    from formlessness.displayers import Display
    from formlessness.validators import Validator


class Keyed(Protocol):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)


class Converter(Keyed, Serializer[D, T], Deserializer[D, T], ABC):
    """
    Things that validate, serialize and deserialize data, like Forms and Fields.
    """

    # Class level defaults for validators. Other validators are in addition.
    # Validators to run at the data and object state, respectively.
    data_validators: Sequence[Validator[D]] = ()
    object_validators: Sequence[Validator[T]] = ()

    def make_object(self, data: D) -> T:
        """
        Turn data into an object (deserialize it), raising ValidationIssueMap if needed.
        """
        self.data_issues(data).raise_if_not_empty()
        obj = self.deserialize(data)
        self.object_issues(obj).raise_if_not_empty()
        return obj

    def data_issues(self, data: D) -> ValidationIssueMap:
        return _validate(self.key, data, self.data_validators)

    def object_issues(self, obj: T) -> ValidationIssueMap:
        return _validate(self.key, obj, self.object_validators)


def _validate(
    key: str, value: Any, validators: Iterable[Validator]
) -> ValidationIssueMap:
    return ValidationIssueMap(
        key,
        [issue for validator in validators for issue in validator.validate(value)],
    )


class Parent(Displayer[JSONDict], Mapping[str, Union["Parent", Converter]], Keyed, ABC):
    """
    A recursive container for form-stuff. This would be a Form or Section.
    """

    children: dict[str, Keyed]
    display_info: Display

    def __getitem__(self, item: str) -> Keyed:
        return self.children[item]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[str]:
        return iter(self.children)

    @property
    def converters(self) -> dict[str, Converter]:
        """
        The children that are Converters, with direct access to the children of non-Convert parents.

        This creates a secondary tree structure (after self.children). This is a tree of Converters, ending
        in a non-Parent (a Field). It's the tree structure for deserialization, serialization, and validation.
        """
        converters = {}
        for key, child in self.children.items():
            if isinstance(child, Converter):
                converters[key] = child
            elif isinstance(child, Parent):
                converters |= child.converters
        return converters

    def converter_to_sub_object(self, obj: T) -> Mapping[Converter, Any]:
        """
        Given an object, breaks it apart and maps it to the children converters.
        Useful for validation and serialization.
        """
        if isinstance(obj, Mapping):
            return {self.converters[k]: v for k, v in obj.items()}
        return {
            child: getattr(obj, attr)
            for attr, child in self.converters.items()
            if hasattr(obj, attr)
        }

    def converter_to_sub_data(self, data: JSONDict) -> Mapping[Converter, JSONData]:
        """
        Given a dictionary, breaks it apart and maps it to the children converters.
        Useful for validation and deserialization.
        """
        return {self.converters[k]: v for k, v in data.items()}

    @property
    def displayers(self) -> Mapping[str, Displayer]:
        return {
            k: child
            for k, child in self.children.items()
            if isinstance(child, Displayer)
        }

    def display(self, data: JSONDict = None, path: list[str] = ()) -> Display:
        data = data or {}
        path = path or []
        display = self.display_info.copy()
        if isinstance(self, Converter):
            path += [self.key]
            display["path"] = path
        children_displays = {}
        for key, child in self.displayers.items():
            sub_data = data.get(key) if isinstance(child, Converter) else data
            children_displays[key] = child.display(sub_data, path)
        display["contents"] = children_displays
        return display
