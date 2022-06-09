"""
The Display is the representation of the Form sent to the frontend.
It's recursive, with every component of a Form also having a Display.
"""


from abc import ABC, abstractmethod
from typing import Generic

from formlessness.types import D, JSONDict

Display = JSONDict


def filter_display_info(display_info: Display) -> Display:
    """
    Helper to remove falsy values.
    """
    return {k: v for k, v in display_info.items() if v}


class Displayer(Generic[D], ABC):
    """
    Things that can create Displays.
    """

    @abstractmethod
    def display(self, object_path: str = "") -> Display:
        """
        object_path is the JSON Pointer to the relevant part of the Converter (Form/Field).
        """
