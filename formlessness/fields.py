from __future__ import annotations

from abc import ABC
from datetime import date
from typing import Iterable, Sequence

from formlessness.abstract_classes import Converter
from formlessness.deserializers import Deserializer, FunctionDeserializer
from formlessness.displayers import Display, Displayer, filter_display_info
from formlessness.serializers import Serializer, serializer as serializer_decorator
from formlessness.types import D, JSONDict, T
from formlessness.utils import key_and_label
from formlessness.validators import (
    And,
    ChoicesValidator,
    Or,
    Validator,
    each_item_is_str,
    is_date,
    is_int,
    is_list,
    is_null,
    is_str,
)
from formlessness.widgets import Widget


class Field(Converter[D, T], Displayer[D], ABC):
    """
    Abstract class. For type checks.
    """


class BasicField(Field[D, T]):
    """
    This can be more specific.
    """

    default_serializer: Serializer
    default_deserializer: Deserializer
    default_widget: Widget
    default_data_validators: tuple[Validator[D], ...] = ()
    default_object_validators: tuple[Validator[T], ...] = ()

    # noinspection PyShadowingNames
    def __init__(
        self,
        label: str = "",
        description: str = "",
        shadow: str = "",
        widget: Widget = None,
        choices: Iterable[T] = (),
        required: bool = True,
        extra_data_validators: Sequence[Validator] = (),
        extra_object_validators: Sequence[Validator] = (),
        serializer: Serializer[D, T] = None,
        deserializer: Deserializer[D, T] = None,
        key: str = "",
    ) -> None:
        key, label = key_and_label(key, label)

        self.serializer = serializer or self.default_serializer
        self.deserializer = deserializer or self.default_deserializer
        self.key = key
        self.data_validators = self.default_data_validators + tuple(
            extra_data_validators
        )
        self.object_validators = self.default_object_validators + tuple(
            extra_object_validators
        )
        self.choices = tuple(choices)
        data_choices = [self.serialize(choice) for choice in self.choices]
        if self.choices:
            self.data_validators += (ChoicesValidator(data_choices),)
            self.object_validators += (ChoicesValidator(self.choices),)
        self.required = required
        if not self.required:
            self.data_validators = [Or([is_null, And(self.data_validators)])]

        self.display_info: JSONDict = filter_display_info(
            {
                "type": "field",
                "label": label,
                "description": description,
                "shadow": shadow,
                "widget": str(widget or self.default_widget),
                "choices": data_choices or None,
            }
        )

    def __str__(self):
        return self.display_info.get("label") or self.key

    def serialize(self, obj: T) -> D:
        return self.serializer.serialize(obj)

    def deserialize(self, data: D) -> T:
        return self.deserializer.deserialize(data)

    def display(self, data: D = None) -> Display:
        if data is None:
            return self.display_info
        return self.display_info | {"value": data}


class IntField(BasicField[int, int]):
    default_serializer = serializer_decorator(int)
    default_deserializer = FunctionDeserializer(int, "Must be an integer.")
    default_data_validators = (is_int,)
    default_object_validators = (is_int,)
    default_widget = Widget.TEXT_BOX


class StrField(BasicField[str, str]):
    default_serializer = serializer_decorator(str)
    default_deserializer = FunctionDeserializer(str, "Must be a string.")
    default_data_validators = (is_str,)
    default_object_validators = (is_str,)
    default_widget = Widget.TEXT_BOX


class DateField(BasicField[str, date]):
    default_serializer = serializer_decorator(lambda d: d.isoformat())
    default_deserializer = FunctionDeserializer(
        date.fromisoformat, "Must be a valid date of YYYY-MM-DD."
    )
    default_data_validators = (is_str,)
    default_object_validators = (is_date,)
    default_widget = Widget.DATE_SELECTOR


class CommaListStrField(BasicField[str, list[str]]):
    default_serializer = serializer_decorator(lambda x: ",".join(x))
    default_deserializer = FunctionDeserializer(
        lambda x: [y for y in x.split(",") if y], "Must be a string."
    )
    default_data_validators = (is_str,)
    default_object_validators = (is_list, each_item_is_str)
    default_widget = Widget.TEXT_BOX
