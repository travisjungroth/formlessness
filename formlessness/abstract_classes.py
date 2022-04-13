from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Generic, Iterable, Mapping, Protocol, Sequence

from formlessness.deserializers import Deserializer
from formlessness.exceptions import ValidationIssueMap
from formlessness.serializers import Serializer
from formlessness.types import D, JSONData, JSONDict, T

if TYPE_CHECKING:
    from formlessness.validators import Validator
    from formlessness.views import ViewMaker
    from formlessness.widgets import Widget


class Keyed(Protocol):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)


class Converter(Serializer, Deserializer, Keyed, ABC, Generic[T, D]):
    """
    Things that validate, serialize and deserialize data, like Forms and Fields.
    """

    # Class level defaults for validators. Other validators are in addition.
    # Validators to run at the data and object state, respectively.
    # The same validator may show up in both if the object is data, like an int.
    data_validators: Sequence[Validator[T]] = ()
    object_validators: Sequence[Validator[T]] = ()

    def make_object(self, data: D) -> T:
        """
        Validation and deserialization. Raises ValidationIssueMap
        """
        self.data_issues(data).raise_if_not_empty()
        obj = self.deserialize(data)
        self.object_issues(obj).raise_if_not_empty()
        return obj

    def data_issues(self, data: D) -> ValidationIssueMap:
        return self._validate(data, self.data_validators)

    def object_issues(self, obj: T) -> ValidationIssueMap:
        return self._validate(obj, self.object_validators)

    def _validate(
        self, obj: Any, validators: Iterable[Validator]
    ) -> ValidationIssueMap:
        return ValidationIssueMap(
            self.key,
            [issue for validator in validators for issue in validator.validate(obj)],
        )


class Parent(Keyed):
    children: dict[str, Keyed]

    @property
    def converters(self) -> dict[str, Converter]:
        converters = {}
        for key, child in self.children.items():
            if isinstance(child, Converter):
                converters[key] = child
            elif hasattr(child, "converters"):  # Sections
                converters |= child.converters
        return converters

    def converter_to_sub_object(self, obj: T) -> Mapping[Converter, Any]:
        if isinstance(obj, Mapping):
            return {self.converters[k]: v for k, v in obj.items()}
        return {
            child: getattr(obj, attr)
            for attr, child in self.converters.items()
            if hasattr(obj, attr)
        }

    def converter_to_sub_data(self, data: JSONDict) -> Mapping[Converter, JSONData]:
        return {self.converters[k]: v for k, v in data.items()}

    # todo: change to ViewInfo style
    title: str = ""
    description: str = ""
    widget: Widget  # Like hidden or collapsible, maybe should be a different class than Widget

    @property
    def own_stuff(self):
        d = {
            "title": self.title,
            "description": self.description,
            "widget": self.widget,
        }
        return {k: v for k, v in d.items() if v}

    @property
    def view_makers(self) -> Mapping[str, ViewMaker]:
        return {
            k: child
            for k, child in self.children.items()
            if isinstance(child, ViewMaker)
        }