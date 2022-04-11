from __future__ import annotations

from abc import ABC
from typing import Callable, Mapping

from formlessness.forms import Converter
from formlessness.exceptions import ValidationIssueMap
from formlessness.types import JSONDict, T
from formlessness.abstract_classes import Parent


class AbstractBasicForm(Parent, Converter, ABC):
    """
    Converts and has other converters.
    """

    def data_issues(self, data: JSONDict) -> ValidationIssueMap:
        return self._validate_form(super().data_issues, self.converter_to_sub_data, data)

    def object_issues(self, obj: T) -> ValidationIssueMap:
        return self._validate_form(super().object_issues, self.converter_to_sub_object, obj)

    def object_issues_skip_data(self, obj: T) -> ValidationIssueMap:
        return self._validate_form(super().object_issues_skip_data, self.converter_to_sub_object, obj)


def _validate_form(
    self,
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
