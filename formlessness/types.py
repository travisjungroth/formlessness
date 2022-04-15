from __future__ import annotations

from typing import TypeVar, Union

JSONData = Union[str, int, float, None, list["JSONData"], dict[str, "JSONData"]]
JSONDict = dict[str, JSONData]
D = TypeVar("D", bound=JSONData)  # TypeVar for the data stage
T = TypeVar("T")  # TypeVar for the object stage
