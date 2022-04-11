from __future__ import annotations

from abc import ABC
from typing import Generic, Iterable, Optional, Sequence

from formlessness.abstract_classes import Converter
from formlessness.deserializers import (
    Deserializer,
    FunctionDeserializer,
    HasDeserializer,
)
from formlessness.serializers import HasSerializer, Serializer
from formlessness.serializers import serializer as serializer_decorator
from formlessness.types import D, T
from formlessness.validators import (
    ChoicesValidator,
    Validator,
    each_item_is_str,
    is_int,
    is_list,
    is_str,
)
from formlessness.views import HasViewMaker
from formlessness.widgets import Widget


class Field(
    Converter[T, D], HasSerializer, HasDeserializer, HasViewMaker, ABC, Generic[T, D]
):
    """
    Abstract class. For type checks.
    """


class BasicField(Field[T, D], Generic[T, D]):
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
        choices: Optional[Iterable[T]] = (),
        extra_data_validators: Sequence[Validator] = (),
        extra_object_validators: Sequence[Validator] = (),
        serializer: Serializer[T, D] = None,
        deserializer: Deserializer[T, D] = None,
        key: str = "",
    ) -> None:
        if not key:
            if not label:
                raise ValueError("Must set key or label.")
            key = "".join([c for c in label.lower() if c.isalnum()])

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
        # todo: only add truthy values
        self.view_info = {
            "label": label,
            "description": description,
            "shadow": shadow,
            "widget": widget or self.default_widget,
            "choices": data_choices,
        }

    def __str__(self):
        return self.view_info.get("label") or self.key


class IntField(BasicField[int, int]):
    default_serializer = serializer_decorator(int)
    default_deserializer = FunctionDeserializer(int, "Must be an integer.")
    default_data_validators: tuple[Validator[D], ...] = (is_int,)
    default_object_validators: tuple[Validator[T], ...] = (is_int,)
    default_widget = Widget.TEXT_BOX


class CommaListStrField(BasicField[list[str], str]):
    default_serializer = serializer_decorator(lambda x: ",".join(x))
    default_deserializer = FunctionDeserializer(
        lambda x: [y for y in x.split(",") if y], "Must be a string."
    )
    default_data_validators: tuple[Validator[D], ...] = (is_str,)
    default_object_validators: tuple[Validator[T], ...] = (is_list, each_item_is_str)
    default_widget = Widget.TEXT_BOX
