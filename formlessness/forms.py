from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING

from formlessness.abstract_classes import Converter, Keyed, Parent
from formlessness.deserializers import Deserializer
from formlessness.displayers import filter_display_info
from formlessness.exceptions import ValidationIssueMap
from formlessness.serializers import Serializer
from formlessness.types import D, JSONDict, T
from formlessness.utils import key_and_label

if TYPE_CHECKING:
    from formlessness.validators import Validator


class Form(Parent, Converter[D, T], ABC):
    """
    Converts and has other converters.
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
        self.data_validators = self.default_data_validators + tuple(
            extra_data_validators
        )
        self.object_validators = self.default_object_validators + tuple(
            extra_object_validators
        )
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

    def data_issues(self, data: JSONDict) -> ValidationIssueMap:
        return _validate_form(super().data_issues, self.converter_to_sub_data, data)

    def object_issues(self, obj: T) -> ValidationIssueMap:
        return _validate_form(super().object_issues, self.converter_to_sub_object, obj)

    def deserialize(self, data: JSONDict) -> T:
        # todo: change to build up ValidationIssueMap on errors

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


def _validate_form(
    validation_method: Callable[[T], ValidationIssueMap],
    mapping_method: Callable[[T], Mapping[Converter, T]],
    value: T,
) -> ValidationIssueMap:
    issue_map = validation_method(value)
    child_issues = []
    for child, child_obj in mapping_method(value).items():
        child_validation_method = getattr(child, validation_method.__name__)
        child_issues.append(child_validation_method(child_obj))
    return issue_map.add_issues(child_issues)
