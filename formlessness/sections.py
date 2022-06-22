from abc import ABC
from collections.abc import Iterable
from typing import Optional

from formlessness.base_classes import Keyed, Converter
from formlessness.displayers import Display
from formlessness.forms import Fixed
from formlessness.utils import key_and_label
from formlessness.utils import remove_null_values


class Section(Fixed, ABC):
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

    def display(self, object_path: str = "") -> Display:
        contents = []
        for key, child in self.children.items():
            if isinstance(child, Converter):
                child_path = f"{object_path}/{key}"
            else:
                child_path = object_path
            contents.append(child.display(child_path))
        return self.display_info | {"contents": contents}