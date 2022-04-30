from typing import TypedDict, Final


class Widget(TypedDict):
    type: str


text: Final[Widget] = Widget(type='text')
date_picker: Final[Widget] = Widget(type='date_picker')
