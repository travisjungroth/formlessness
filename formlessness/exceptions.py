from typing import Any, Mapping


class FormErrors(Exception):
    """
    :param issues_map: A mapping from a path of keys to something that can have str called on it.
    """

    def __init__(self, issues_map: Mapping[tuple[str, ...], Any]):
        self.issues_map = issues_map

    def as_dict(self) -> dict[str, str]:
        return {".".join(k): str(v) for k, v in self.issues_map.items()}


class DeserializationError(Exception):
    pass
