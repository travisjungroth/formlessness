from typing import TypeVar, Union

JSONData = Union[str, int, float, list["JSONData"], dict[str, "JSONData"], None]
JSONDict = dict[str, JSONData]
D = TypeVar("D", bound=JSONData)  # TypeVar for the data stage
T = TypeVar("T")  # TypeVar for the object stage
