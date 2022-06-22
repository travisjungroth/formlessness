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


class FixedMappingForm(Fixed, Form[JSONDict, dict]):
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
        serializer: Serializer[D, T] = Serializer(),
        deserializer: Deserializer[D, T] = Deserializer(),
        key: str = "",
        children: Sequence[Keyed] = (),
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.serializer = serializer
        self.deserializer = deserializer
        self.children = {child.key: child for child in children}
        self.default = default
        self.default_data = MISSING if default is MISSING else self.serialize(default)
        self.data_constraint &= And(
            *extra_data_constraints, HasKeys(self.required_keys())
        )
        self.object_constraint &= And(*extra_object_constraints)
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
        # todo move out to deserializer
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
                # in the resultant map, to avoid passing path
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

    def pre_serialize(self, obj: T) -> dict[str, Any]:
        # todo: move out to Serializers.
        converters = self.converters()
        if isinstance(obj, Mapping):
            g = ((k, obj[k]) for k in converters.keys() if k in obj)
        else:
            g = ((attr, getattr(obj, attr)) for attr in converters.keys())
        return {key: converters[key].serialize(sub_object) for key, sub_object in g}

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
        data = self.pre_serialize(obj)
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

    def inner_data_schema(self) -> JSONDict:
        return {
            "type": "object",
            "properties": {
                k: v.inner_data_schema() for k, v in self.converters().items()
            },
            "required": self.required_keys(),
            "unevaluatedProperties": False,
        } | super().inner_data_schema()

    def required_keys(self) -> list[str]:
        return [k for k, converter in self.converters().items() if converter.required]


class FixedListForm:
    """Could this mostly be a fixed mapping with int keys?"""

    contents: list  # converter or list_section
    order: list[int]


class VariableMappingForm:
    """"""

    converter: Converter  # acts as the reference


class VariableListForm(Form[D, T]):
    """"""

    def __init__(
        self,
        content: Converter,
        label: Optional[str] = None,
        description: Optional[str] = None,
        collapsable: bool = False,
        collapsed: bool = False,
        default: Union[T, object] = MISSING,
        required: bool = True,
        nullable: bool = False,
        extra_data_constraints: Sequence[Constraint] = (),
        extra_object_constraints: Sequence[Constraint] = (),
        serializer: Serializer[D, T] = Serializer(),
        deserializer: Deserializer[D, T] = Deserializer(),
        key: str = "",
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.serializer = serializer
        self.deserializer = deserializer
        self.content = content
        self.default = default
        self.default_data = MISSING if default is MISSING else self.serialize(default)
        self.data_constraint &= And(*extra_data_constraints)
        self.object_constraint &= And(*extra_object_constraints)
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
                "type": "variable_list_form",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )

    def _validate_sub_data(self, data: list) -> dict[str, ConstraintMap]:
        return {
            str(i): self.content.validate_data(sub_data)
            for i, sub_data in enumerate(data)
        }

    def _validate_sub_objects(self, obj: list) -> Mapping[str, ConstraintMap]:
        return {
            str(i): self.content.validate_object(sub_obj)
            for i, sub_obj in enumerate(obj)
        }

    def deserialize(self, data: JSONDict, path: Sequence[str] = ()) -> T:
        # todo: move to a deserializer
        errors = {}
        new_data = []
        for i, sub_data in enumerate(data):
            try:
                new_data.append(self.content.deserialize(sub_data))
            except FormErrors as e:
                errors |= e.issues_map
            except DeserializationError as e:
                errors[tuple([*path, str(i)])] = e

        if errors:
            raise FormErrors(errors)

        try:
            return self.deserializer.deserialize(new_data)
        except DeserializationError as e:
            raise FormErrors({tuple(path): e})

    def serialize(self, obj: list) -> list[JSONDict]:
        return [self.content.serialize(x) for x in obj]

    def display(self, object_path: str = "") -> Display:
        return self.display_info | {
            "objectPath": object_path,
            "content": self.content.display(f"{object_path}/*"),
        }

    def inner_data_schema(self) -> JSONDict:
        # Todo add array stuff
        return {
            "type": "array",
        } | super().inner_data_schema()
