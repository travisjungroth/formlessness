from abc import ABC
from collections.abc import Iterable
from typing import Optional

from formlessness.base_classes import Keyed
from formlessness.base_classes import Parent
from formlessness.utils import key_and_label, remove_null_values


class Section(Parent, ABC):
    """
    Arbitrary section of a form. Not a Converter.
    """


class BasicSection(Section):
    def __init__(
        self,
        label: Optional[str] = None,
        description: Optional[str] = None,
        collapsable: bool = False,
        collapsed: bool = False,
        key: str = "",
        children: Iterable[Keyed] = (),
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.display_info = remove_null_values(
            {
                "type": "section",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )
        self.children = {child.key: child for child in children}
