from __future__ import annotations

from abc import ABC

from formlessness.abstract_classes import Keyed


class Section(UIParent, HasFrontendMaker, Keyed, ABC):
    """
    Arbitrary section. Not a Converter.
    """