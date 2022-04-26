from __future__ import annotations

from abc import ABC
from collections.abc import Iterable

from formlessness.base_classes import Keyed, Parent
from formlessness.displayers import filter_display_info
from formlessness.utils import key_and_label


class Section(Parent, ABC):
    """
    Arbitrary section of a form. Not a Converter.
    """


class BasicSection(Section):
    def __init__(
        self,
        label: str = "",
        description: str = "",
        collapsable: bool = False,
        collapsed: bool = False,
        key: str = "",
        children: Iterable[Keyed] = (),
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.display_info = filter_display_info(
            {
                "type": "section",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )
        self.children = {child.key: child for child in children}
