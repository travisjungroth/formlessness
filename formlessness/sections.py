from __future__ import annotations

from abc import ABC

from formlessness.abstract_classes import Keyed, Parent
from formlessness.views import HasViewMaker


class Section(Parent, HasViewMaker, Keyed, ABC):
    """
    Arbitrary section. Not a Converter.
    """
