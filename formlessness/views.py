from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from formlessness.abstract_classes import Keyed
from formlessness.exceptions import ValidationIssueMap
from formlessness.types import D, JSONDict, T

View = JSONDict
ViewInfo = JSONDict


@runtime_checkable
class ViewMaker(Keyed, Protocol[T, D]):
    """
    If you wanted to make a totally weird view that didn't match the tree structure of the object, you could.
    """

    @abstractmethod
    def into_view(self) -> View:
        pass

    @abstractmethod
    def data_into_view(self, data: D, issue_map: ValidationIssueMap = None) -> View:
        pass

    @abstractmethod
    def object_into_view(self, obj: T, issue_map: ValidationIssueMap = None) -> View:
        pass


class HasViewMaker(ViewMaker, Protocol):
    """
    Proxy a ViewMaker
    """

    view_maker: ViewMaker

    def into_view(self) -> View:
        return self.view_maker.into_view()

    def data_into_view(self, data: D, issue_map: ValidationIssueMap = None) -> View:
        return self.view_maker.data_into_view(data, issue_map)

    def object_into_view(self, obj: T, issue_map: ValidationIssueMap = None) -> View:
        return self.view_maker.object_into_view(obj, issue_map)
