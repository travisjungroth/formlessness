from __future__ import annotations

from typing import Union, TypeVar

JSONData = Union[str, int, float, None, list['JSONData'], dict[str, 'JSONData']]
JSONDict = dict[str, JSONData]
D = TypeVar('D', bound=JSONData)
T = TypeVar('T')
