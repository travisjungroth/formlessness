from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Union

from formlessness.base_classes import Converter
from formlessness.base_classes import Keyed
from formlessness.constraints import And
from formlessness.constraints import Constraint
from formlessness.constraints import ConstraintMap
from formlessness.constraints import HasKeys
from formlessness.constraints import is_null
from formlessness.constraints import not_null
from formlessness.deserializers import Deserializer
from formlessness.displayers import Display
from formlessness.displayers import Displayer
from formlessness.exceptions import DeserializationError
from formlessness.exceptions import FormErrors
from formlessness.serializers import Serializer
from formlessness.types import D
from formlessness.types import JSONDict
from formlessness.types import T
from formlessness.utils import MISSING
from formlessness.utils import key_and_label
from formlessness.utils import remove_null_values

"""
What are the differences between forms and fields?
Fields have widgets
Could field extend forms?
Could forms have widgets?
Forms could have widgets, or something widget-like! Like collapsable.
"""


class Form(Converter[D, T], Displayer, ABC):
    display_info: Display = {}

    def validate_data(self, data: D) -> ConstraintMap:
        return ConstraintMap(
            top_constraint=self.data_constraint.validate(data),
            child_constraints=self._validate_sub_data(data),
        )

    @abstractmethod
    def _validate_sub_data(self, data: D) -> dict[str, ConstraintMap]:
        pass

    def validate_object(self, obj: T) -> ConstraintMap:
        return ConstraintMap(
            top_constraint=self.object_constraint.validate(obj),
            child_constraints=self._validate_sub_objects(obj),
        )

    @abstractmethod
    def _validate_sub_objects(self, obj: T) -> ConstraintMap:
        pass


class Fixed:
    children: dict[str, Union[Converter, Fixed]]
    order: list[str]

    def converters(self) -> dict[str, Converter]:
        converters = {}
        for key, child in self.children.items():
            if isinstance(child, Converter):
                converters[key] = child
            elif isinstance(child, Fixed):
                converters |= child.converters()
        return converters


class Section(Fixed):
    pass


class FixedMappingForm(Fixed, Form[JSONDict, dict]):
    """Basic form."""

    # Defaults for instances of this class. Meant to be overridden by subclasses.
    default_serializer: Serializer = Serializer()
    default_deserializer: Deserializer = Deserializer()
    default_data_constraints: tuple[Constraint[JSONDict], ...] = ()
    default_object_constraints: tuple[Constraint[T], ...] = ()
    # See schemas/basic_form.json for the JSON Schema of the Display.

    def __init__(
        self,
        label: Optional[str] = None,
        description: Optional[str] = None,
        collapsable: bool = False,
        collapsed: bool = False,
        default: Union[T, object] = MISSING,
        required: bool = True,
        nullable: bool = False,
        extra_data_constraints: Sequence[Constraint] = (),
        extra_object_constraints: Sequence[Constraint] = (),
        serializer: Serializer[D, T] = None,
        deserializer: Deserializer[D, T] = None,
        key: str = "",
        children: Sequence[Keyed] = (),
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.serializer = serializer or self.default_serializer
        self.deserializer = deserializer or self.default_deserializer
        self.children = {child.key: child for child in children}
        self.default = default
        self.default_data = MISSING if default is MISSING else self.serialize(default)
        self.data_constraint &= And(
            *self.default_data_constraints,
            *extra_data_constraints,
            HasKeys(self.required_keys()),
        )
        self.object_constraint &= And(
            *self.default_object_constraints, *extra_object_constraints
        )
        self.required = required
        self.nullable = nullable
        if self.nullable:
            self.data_constraint |= is_null
            self.object_constraint |= is_null
        else:
            self.data_constraint &= not_null
            self.object_constraint &= not_null
        self.display_info = remove_null_values(
            {
                "type": "form",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )

    def deserialize(self, data: JSONDict, path: Sequence[str] = ()) -> T:
        # todo split this into prep_deserialize or something
        new_data = {}
        errors = {}
        for key, child in self.converters().items():
            if key not in data:
                if child.default is MISSING:
                    continue
                new_data[key] = child.default
                continue

            try:
                # todo: could catch the errors and prepend to keys
                new_data[key] = child.deserialize(data[key], [*path, key])
            except FormErrors as e:
                errors |= e.issues_map
            except DeserializationError as e:
                errors[tuple([*path, key])] = e

        if errors:
            raise FormErrors(errors)

        try:
            return self.deserializer.deserialize(new_data)
        except DeserializationError as e:
            raise FormErrors({tuple(path): e})

    def converter_to_sub_object(self, obj: T) -> Mapping[Converter, Any]:
        """
        Given an object, breaks it apart and maps it to the children converters.
        Useful for validation and serialization.
        """
        if isinstance(obj, Mapping):
            converters = self.converters()
            return {converters[k]: v for k, v in obj.items()}
        return {
            child: getattr(obj, attr)
            for attr, child in self.converters().items()
            if hasattr(obj, attr)
        }

    def _validate_sub_data(self, data: JSONDict) -> Mapping[str, ConstraintMap]:
        return {
            key: child.validate_data(data[key])
            for key, child in self.converters().items()
            if key in data
        }

    def _validate_sub_objects(self, obj: T) -> Mapping[str, ConstraintMap]:
        d = {}
        for key, child in self.converters().items():
            if isinstance(obj, Mapping) and key in obj:
                d[key] = child.validate_object(obj[key])
            elif hasattr(obj, key):
                d[key] = child.validate_object(getattr(obj, key))
        return d

    def serialize(self, obj: T) -> JSONDict:
        data: JSONDict = {}
        for child, sub_obj in self.converter_to_sub_object(obj).items():
            data[child.key] = child.serialize(sub_obj)
        return self.serializer.serialize(data)

    def display(self, object_path: str = "") -> Display:
        contents = []
        for key, child in self.children.items():
            if isinstance(child, Converter):
                child_path = f"{object_path}/{key}"
            else:
                child_path = object_path
            contents.append(child.display(child_path))
        return self.display_info | {"objectPath": object_path, "contents": contents}

    def _data_schema(self) -> JSONDict:
        return {
            "type": "object",
            "properties": {k: v._data_schema() for k, v in self.converters().items()},
            "required": self.required_keys(),
            "unevaluatedProperties": False,
        } | super()._data_schema()

    def required_keys(self) -> list[str]:
        return [k for k, converter in self.converters().items() if converter.required]

    def data_schema(self) -> JSONDict:
        return self._data_schema() | {
            "$schema": "http://json-schema.org/draft-07/schema#",
        }


class FixedListForm:
    """Could this mostly be a fixed mapping with int keys?"""

    contents: list  # converter or list_section
    order: list[int]


class VariableMappingForm:
    """"""

    converter: Converter  # acts as the reference


class VariableListForm:
    """"""

    converter: Converter
