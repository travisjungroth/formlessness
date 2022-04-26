"""
The Display is the representation of the Form sent to the frontend.
It's recursive, with every component of a Form also having a Display.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Sequence

from formlessness.types import D, JSONDict

Display = JSONDict


def filter_display_info(display_info: Display) -> Display:
    """
    Helper to remove falsey values.
    """
    return {k: v for k, v in display_info.items() if v}


class Displayer(Generic[D], ABC):
    """
    If you wanted to make a totally weird view that didn't match the tree structure of the object, you could.
    """

    @abstractmethod
    def display(self, data: D = None, path: Sequence[str] = ()) -> Display:
        """
        data is the values that will go into a complete or partial form.
        path is the sequence of keys to get to this Form/Field. Along with its key, creates a unique identity.
        """
