from __future__ import annotations

from abc import ABC

from formlessness.abstract_classes import Keyed, Parent
from formlessness.displayers import Displayer


class Section(Parent, Displayer, Keyed, ABC):
    """
    Arbitrary section. Not a Converter.
    """
