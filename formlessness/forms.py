from abc import ABC
from collections.abc import Sequence
from typing import Optional

from formlessness.base_classes import Converter
from formlessness.base_classes import Keyed
from formlessness.base_classes import Parent
from formlessness.constraints import And
from formlessness.constraints import Constraint
from formlessness.constraints import ConstraintMap
from formlessness.constraints import is_null
from formlessness.constraints import not_null
from formlessness.deserializers import Deserializer
from formlessness.exceptions import DeserializationError
from formlessness.exceptions import FormErrors
from formlessness.serializers import Serializer
from formlessness.types import D
from formlessness.types import JSONDict
from formlessness.types import T
from formlessness.utils import key_and_label
from formlessness.utils import remove_null_values


class Form(Parent, Converter[D, T], ABC):
    """
    Fields serialize objects, deserialize data, and generate their own Display.

    They are different from Fields in that they're Parents i.e. they can contain Field, Forms and Sections.
    This abstract class exists for type checking and if you want to deviate from the implementation of BasicForm.
    """


class BasicForm(Form[JSONDict, T]):
    # Defaults for instances of this class. Meant to be overridden by subclasses.
    default_serializer: Serializer
    default_deserializer: Deserializer
    default_data_constraints: tuple[Constraint[JSONDict], ...] = ()
    default_object_constraints: tuple[Constraint[T], ...] = ()

    def __init__(
        self,
        label: Optional[str] = None,
        description: Optional[str] = None,
        collapsable: bool = False,
        collapsed: bool = False,
        required: bool = True,
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
        if self.required:
            self.data_constraint &= not_null
            self.object_constraint &= not_null
        else:
            self.data_constraint |= is_null
            self.object_constraint |= is_null
        self.data_constraint = And(
            *self.default_data_constraints, *extra_data_constraints
        ).simplify()
        self.object_constraint = And(
            *self.default_object_constraints, *extra_object_constraints
        ).simplify()
        self.display_info = remove_null_values(
            {
                "type": "form",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )
        self.children = {child.key: child for child in children}

    def validate_data(self, data: JSONDict) -> ConstraintMap:
        child_constraints = {}
        for child, child_data in self.converter_to_sub_data(data).items():
            child_constraints[child.key] = child.validate_data(child_data)
        return super().validate_data(data) & ConstraintMap(
            child_constraints=child_constraints
        )

    def validate_object(self, obj: T) -> ConstraintMap:
        child_constraints = {}
        for child, child_data in self.converter_to_sub_object(obj).items():
            child_constraints[child.key] = child.validate_object(child_data)
        return super().validate_object(obj) & ConstraintMap(
            child_constraints=child_constraints
        )

    def deserialize(self, data: JSONDict, path: Sequence[str] = ()) -> T:
        new_data = {}
        errors = {}
        for child, sub_data in self.converter_to_sub_data(data).items():
            try:
                new_data[child.key] = child.deserialize(sub_data, [*path, child.key])
            except FormErrors as e:
                errors |= e.issues_map
            except DeserializationError as e:
                errors[tuple([*path, child.key])] = e
        if errors:
            raise FormErrors(errors)
        try:
            return self.deserializer.deserialize(new_data)
        except DeserializationError as e:
            raise FormErrors({tuple(path): e})

    def serialize(self, obj: T) -> JSONDict:
        data: JSONDict = {}
        for child, sub_obj in self.converter_to_sub_object(obj):
            data[child.key] = child.serialize(sub_obj)
        return self.serializer.serialize(data)

    def _data_schema(self) -> JSONDict:
        return {
            "type": "object",
            "properties": {k: v._data_schema() for k, v in self.converters.items()},
            "required": [
                k for k, converter in self.converters.items() if converter.required
            ],
            "unevaluatedProperties": False,
        }
