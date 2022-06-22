from abc import ABC
from collections.abc import Sequence
from typing import Protocol
from typing import Union

from formlessness.constraints import Constraint
from formlessness.constraints import ConstraintMap
from formlessness.constraints import Valid
from formlessness.constraints import constraint_to_json
from formlessness.deserializers import Deserializer
from formlessness.exceptions import FormErrors
from formlessness.serializers import Serializer
from formlessness.types import D
from formlessness.types import JSONDict
from formlessness.types import T
from formlessness.utils import MISSING


class Keyed(Protocol):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)


class Converter(Serializer[D, T], Deserializer[D, T], ABC):
    """
    Things that validate, serialize and deserialize data, like Forms and Fields.
    """

    data_constraint: Constraint[D] = Valid
    object_constraint: Constraint[T] = Valid
    required: bool = True
    default: Union[T, object] = MISSING
    default_data: Union[D, object] = MISSING

    def make_object(self, data: D) -> T:
        """
        Turn data into an object (deserialize it), raising FormErrors if needed.
        """
        constraint_map = self.validate_data(data)
        if not constraint_map:
            raise FormErrors(constraint_map)
        obj = self.deserialize(data)
        constraint_map = self.validate_object(obj)
        if not constraint_map:
            raise FormErrors(constraint_map)
        return obj

    def deserialize(self, data: D, path: Sequence[str] = ()) -> T:
        return super().deserialize(data)

    def validate_data(self, data: D) -> ConstraintMap:
        return ConstraintMap(self.data_constraint.validate(data))

    def validate_object(self, obj: T) -> ConstraintMap:
        return ConstraintMap(self.object_constraint.validate(obj))

    def inner_data_schema(self) -> JSONDict:
        schema = constraint_to_json(self.data_constraint)
        if self.default is not MISSING:
            schema["default"] = self.default_data
        return schema

    def data_schema(self) -> JSONDict:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
        } | self.inner_data_schema()
