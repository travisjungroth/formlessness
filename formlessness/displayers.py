"""
The Display is the representation of the Form sent to the frontend.
It's recursive, with every component of a Form also having a Display.
"""


from abc import ABC
from abc import abstractmethod
from typing import Generic

from formlessness.types import D
from formlessness.types import JSONDict

Display = JSONDict


class Displayer(Generic[D], ABC):
    """
    Things that can create Displays.
    """

    @abstractmethod
    def display(self, object_path: str = "") -> Display:
        """
        object_path is the JSON Pointer to the relevant part of the Converter (Form/Field).
        """
