from abc import ABC
from typing import Any
from typing import Iterator
from typing import Mapping
from typing import Protocol
from typing import Union

from formlessness.constraints import Constraint
from formlessness.constraints import ConstraintMap
from formlessness.constraints import Valid
from formlessness.deserializers import Deserializer
from formlessness.displayers import Display
from formlessness.displayers import Displayer
from formlessness.exceptions import FormErrors
from formlessness.serializers import Serializer
from formlessness.types import D
from formlessness.types import JSONData
from formlessness.types import JSONDict
from formlessness.types import T


class Keyed(Protocol):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)


class Converter(Keyed, Serializer[D, T], Deserializer[D, T], ABC):
    """
    Things that validate, serialize and deserialize data, like Forms and Fields.
    """

    data_constraint: Constraint[D] = Valid
    object_constraint: Constraint[T] = Valid
    required: bool = True

    def make_object(self, data: D) -> T:
        """
        Turn data into an object (deserialize it), raising FormErrors if needed.
        """
        constraint_map = self.validate_data(data)
        if not constraint_map:
            raise FormErrors(constraint_map)
        obj = self.deserialize(data)
        constraint_map = self.validate_object(obj)
        if not constraint_map:
            raise FormErrors(constraint_map)
        return obj

    def validate_data(self, data: D) -> ConstraintMap:
        return ConstraintMap(self.data_constraint.validate(data))

    def data_is_valid(self, data: D) -> bool:
        return bool(self.data_constraint.validate(data))

    def validate_object(self, obj: T) -> ConstraintMap:
        return ConstraintMap(self.object_constraint.validate(obj))

    def object_is_valid(self, obj: T) -> bool:
        return bool(self.data_constraint.validate(obj))

    def data_schema(self) -> JSONDict:
        """Experimental and would break with Not"""
        return self._data_schema() | {
            "$schema": "http://json-schema.org/draft-07/schema#",
        }

    def _data_schema(self) -> JSONDict:
        schema = self.data_constraint.json_schema()
        return schema if schema is not None else {}


class Parent(Displayer[JSONDict], Keyed, Mapping[str, Union["Parent", Converter]], ABC):
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

    def display(self, object_path: str = "") -> Display:
        display = self.display_info.copy()
        if isinstance(self, Converter):
            display["objectPath"] = object_path
        display["contents"] = []
        for key, child in self.displayers.items():
            child_path = (
                f"{object_path}/{key}" if isinstance(child, Converter) else object_path
            )
            display["contents"].append(child.display(child_path))
        return display
