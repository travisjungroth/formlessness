from typing import Final
from typing import TypedDict
class Widget(TypedDict):
    type: str


text: Final[Widget] = Widget(type="text")
text_area: Final[Widget] = Widget(type="text_area")
date_picker: Final[Widget] = Widget(type="date_picker")
checkbox: Final[Widget] = Widget(type="checkbox")
