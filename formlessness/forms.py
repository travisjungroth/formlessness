from __future__ import annotations

from abc import ABC
from collections.abc import Iterable, Sequence

from formlessness.abstract_classes import Converter, Keyed, Parent
from formlessness.deserializers import Deserializer
from formlessness.displayers import filter_display_info
from formlessness.serializers import Serializer
from formlessness.types import D, JSONDict, T
from formlessness.utils import key_and_label
from formlessness.validators import And, Validator, ValidatorMap


class Form(Parent, Converter[D, T], ABC):
    """
    Abstract class for type hints.
    """


class BasicForm(Form[JSONDict, T]):
    default_serializer: Serializer
    default_deserializer: Deserializer
    default_data_validators: tuple[Validator[JSONDict], ...] = ()
    default_object_validators: tuple[Validator[T], ...] = ()

    def __init__(
        self,
        label: str = "",
        description: str = "",
        collapsable: bool = False,
        collapsed: bool = False,
        extra_data_validators: Sequence[Validator] = (),
        extra_object_validators: Sequence[Validator] = (),
        serializer: Serializer[D, T] = None,
        deserializer: Deserializer[D, T] = None,
        key: str = "",
        children: Iterable[Keyed] = (),
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.serializer = serializer or self.default_serializer
        self.deserializer = deserializer or self.default_deserializer
        self.data_validator = And(
            [*self.default_data_validators, *extra_data_validators]
        ).simplify()
        self.object_validator = And(
            [*self.default_object_validators, *extra_object_validators]
        ).simplify()
        self.display_info = filter_display_info(
            {
                "type": "form",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )
        self.children = {child.key: child for child in children}

    def validate_data(self, data: JSONDict) -> ValidatorMap:
        sub_maps = {}
        for child, child_data in self.converter_to_sub_data(data).items():
            sub_maps[child.key] = child.validate_data(child_data)
        return super().validate_data(data) & ValidatorMap(sub_maps=sub_maps)

    def validate_object(self, obj: T) -> ValidatorMap:
        sub_maps = {}
        for child, child_data in self.converter_to_sub_object(obj).items():
            sub_maps[child.key] = child.validate_object(child_data)
        return super().validate_object(obj) & ValidatorMap(sub_maps=sub_maps)

    def deserialize(self, data: JSONDict) -> T:
        # Todo: build and raise ErrorMap
        data = {
            child.key: child.deserialize(sub_data)
            for child, sub_data in self.converter_to_sub_data(data).items()
        }
        return self.deserializer.deserialize(data)

    def serialize(self, obj: T) -> JSONDict:
        data: JSONDict = {}
        for child, sub_obj in self.converter_to_sub_object(obj):
            data[child.key] = child.serialize(sub_obj)
        return self.serializer.serialize(data)
