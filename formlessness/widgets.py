from __future__ import annotations

from enum import Enum


class Widget(str, Enum):
    """Text area, multi select, etc."""

    TEXT_BOX = "text_box"
    DATE_SELECTOR = "date_selector"

    def __str__(self):
        return self.value
