from __future__ import annotations

from typing import Any, Mapping


class FormErrors(Exception):
    def __init__(self, error_map: Mapping[tuple[str, ...], Any]):
        self.error_map = error_map

    def as_dict(self) -> dict[str, str]:
        return {".".join(k): str(v) for k, v in self.error_map.items()}


class SerializationError(Exception):
    pass
