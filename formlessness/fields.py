from abc import ABC
from datetime import date, datetime, time
from typing import Iterable, Sequence

from formlessness.base_classes import Converter
from formlessness.constraints import (
    And,
    Choices,
    Constraint,
    EachItem,
    OfType,
    is_date,
    is_datetime,
    is_float,
    is_int,
    is_list_of_int,
    is_list_of_str,
    is_null,
    is_str,
    is_time,
)
from formlessness.deserializers import (
    Deserializer,
    FunctionDeserializer,
    SplitDeserializer,
    date_from_iso_str,
    datetime_from_iso_str,
    time_from_iso_str,
)
from formlessness.displayers import Display, Displayer, filter_display_info
from formlessness.serializers import (
    FunctionSerializer,
    JoinSerializer,
    Serializer,
    isoformat,
)
from formlessness.types import D, JSONDict, T
from formlessness.utils import attrs_to_path, key_and_label
from formlessness.widgets import Widget, date_picker, text


class Field(Converter[D, T], Displayer[D], ABC):
    """
    Fields serialize objects, deserialize data, and generate their own Display.

    They are different from Forms in that they're not Parents i.e. they don't contain Fields, Forms or Sections.
    This abstract class exists for type checking and if you want to deviate from the implementation of BasicField.
    """


class BasicField(Field[D, T]):
    """
    You can create a Field directly from this class, or subclass it to make a template.
    """

    # Defaults for instances of this class. Meant to be overridden by subclasses.
    default_serializer: Serializer
    default_deserializer: Deserializer
    default_widget: Widget
    default_data_constraints: tuple[Constraint[D], ...] = ()
    default_object_constraints: tuple[Constraint[T], ...] = ()

    def __init__(
        self,
        # Data to pass to the Display
        label: str = "",
        description: str = "",
        shadow: str = "",
        widget: Widget = None,
        # Choices are included in the Display and will add a Choices.
        choices: Iterable[T] = (),
        # Adds a not_null Criteria
        required: bool = True,
        # These constraints are added to the class defaults to create the two Constraints.
        extra_data_constraints: Sequence[Constraint] = (),
        extra_object_constraints: Sequence[Constraint] = (),
        serializer: Serializer[D, T] = None,
        deserializer: Deserializer[D, T] = None,
        key: str = "",
    ) -> None:
        key, label = key_and_label(key, label)
        self.serializer = serializer or self.default_serializer
        self.deserializer = deserializer or self.default_deserializer
        self.key = key
        self.data_constraint = And(
            *self.default_data_constraints, *extra_data_constraints
        )
        self.object_constraint = And(
            *self.default_object_constraints, *extra_object_constraints
        )
        self.choices = tuple(choices)
        data_choices = [self.serialize(choice) for choice in self.choices]
        if self.choices:
            self.data_constraint &= Choices(data_choices)
            self.object_constraint &= Choices(self.choices)
        self.required = required
        if not self.required:
            self.data_constraint |= is_null
            self.object_constraint |= is_null
        self.data_constraint = self.data_constraint.simplify()
        self.object_constraint = self.object_constraint.simplify()

        self.display_info: JSONDict = filter_display_info(
            {
                "type": "field",
                "label": label,
                "description": description,
                "shadow": shadow,
                "widget": widget or self.default_widget,
                "choices": data_choices or None,
            }
        )

    def __str__(self):
        return self.display_info.get("label") or self.key

    def serialize(self, obj: T) -> D:
        return self.serializer.serialize(obj)

    def deserialize(self, data: D, path: Sequence[str] = ()) -> T:
        return self.deserializer.deserialize(data)

    def display(self, object_path: Iterable[str] = ()) -> Display:
        return self.display_info | {"objectPath": attrs_to_path(object_path)}


class IntField(BasicField[int, int]):
    default_serializer = FunctionSerializer(int)
    default_deserializer = FunctionDeserializer(int, "Must be an integer.")
    default_data_constraints = (is_int,)
    default_object_constraints = (is_int,)
    default_widget = text


class FloatField(BasicField[float, float]):
    default_serializer = FunctionSerializer(float)
    default_deserializer = FunctionDeserializer(float, "Must be a float.")
    default_data_constraints = (is_float,)
    default_object_constraints = (is_float,)
    default_widget = text


class StrField(BasicField[str, str]):
    default_serializer = FunctionSerializer(str)
    default_deserializer = FunctionDeserializer(str, "Must be a string.")
    default_data_constraints = (is_str,)
    default_object_constraints = (is_str,)
    default_widget = text


class DateField(BasicField[str, date]):
    default_serializer = isoformat
    default_deserializer = date_from_iso_str
    default_data_constraints = (is_str,)
    default_object_constraints = (is_date,)
    default_widget = date_picker


class DateTimeField(BasicField[str, datetime]):
    default_serializer = isoformat
    default_deserializer = datetime_from_iso_str
    default_data_constraints = (is_str,)
    default_object_constraints = (is_datetime,)
    default_widget = date_picker


class TimeField(BasicField[str, time]):
    default_serializer = isoformat
    default_deserializer = time_from_iso_str
    default_data_constraints = (is_str,)
    default_object_constraints = (is_time,)
    default_widget = date_picker


# TODO: Add BoolField
# TODO: Add JSONField


class CommaListStrField(BasicField[str, list[str]]):
    default_serializer = JoinSerializer(",")
    default_deserializer = SplitDeserializer(",")
    default_data_constraints = (is_str,)
    default_object_constraints = (is_list_of_str,)
    default_widget = text


class CommaListIntField(BasicField[str, list[int]]):
    default_serializer = JoinSerializer(",")
    default_deserializer = SplitDeserializer(
        ",", cast_items=int, error_message="Must be a list of integers."
    )
    default_data_constraints = (is_str,)
    default_object_constraints = (is_list_of_int,)
    default_widget = text


def seperated_field(
    separator: str, items_type: type = str, iterable_type: type = list, **kwargs
) -> BasicField:
    d = dict(
        serializer=JoinSerializer(separator),
        deserializer=SplitDeserializer(separator, items_type, iterable_type),
        extra_data_constraints=[is_str] + kwargs.pop("extra_data_constraints", []),
        extra_object_constraints=[
            OfType.get(iterable_type),
            EachItem(OfType.get(items_type)),
        ]
        + kwargs.pop("extra_object_constraints", []),
        widget=text,
    )
    return BasicField(**(d | kwargs))
