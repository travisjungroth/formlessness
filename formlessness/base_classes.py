from abc import ABC
from typing import Any, Iterator, Mapping, Protocol, Union

from formlessness.constraints import Constraint, ConstraintMap, Valid
from formlessness.deserializers import Deserializer
from formlessness.displayers import Display, Displayer
from formlessness.exceptions import FormErrors
from formlessness.serializers import Serializer
from formlessness.types import D, JSONData, JSONDict, T


class Keyed(Protocol):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)


class Converter(Keyed, Serializer[D, T], Deserializer[D, T], ABC):
    """
    Things that validate, serialize and deserialize data, like Forms and Fields.
    """

    # Class level defaults for constraints. Other constraints are in addition.
    # Constraint to validate at the data and object state, respectively.
    # This each of these is a single Constraint. Multiple Constraints are represented with constraints.And.
    data_constraint: Constraint[D] = Valid
    object_constraint: Constraint[T] = Valid

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

    def validate_object(self, obj: T) -> ConstraintMap:
        return ConstraintMap(self.object_constraint.validate(obj))


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
            display["path"] = path
        children_displays = {}
        for key, child in self.displayers.items():
            if isinstance(child, Converter):
                children_displays[key] = child.display(data.get(key), path + [key])
            else:
                children_displays[key] = child.display(data, path)
        display["contents"] = children_displays
        return display
