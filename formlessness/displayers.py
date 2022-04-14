from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from formlessness.types import D, JSONDict

Display = JSONDict


def filter_display_info(display_info: Display) -> Display:
    return {k: v for k, v in display_info.items() if v}


class Displayer(Generic[D], ABC):
    """
    If you wanted to make a totally weird view that didn't match the tree structure of the object, you could.
    """

    @abstractmethod
    def display(self, data: D = None) -> Display:
        pass
