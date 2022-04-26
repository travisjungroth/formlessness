from abc import ABC
from collections.abc import Sequence

from formlessness.base_classes import Converter, Keyed, Parent
from formlessness.constraints import And, Constraint, ConstraintMap
from formlessness.deserializers import Deserializer
from formlessness.displayers import filter_display_info
from formlessness.serializers import Serializer
from formlessness.types import D, JSONDict, T
from formlessness.utils import key_and_label


class Form(Parent, Converter[D, T], ABC):
    """
    Fields serialize objects, deserialize data, and generate their own Display.

    They are different from Fields in that they're Parents i.e. they can contain Field, Forms and Sections.
    This abstract class exists for type checking and if you want to deviate from the implementation of BasicForm.
    """


class BasicForm(Form[JSONDict, T]):
    # Defaults for instances of this class. Meant to be overridden by subclasses.
    default_serializer: Serializer
    default_deserializer: Deserializer
    default_data_constraints: tuple[Constraint[JSONDict], ...] = ()
    default_object_constraints: tuple[Constraint[T], ...] = ()

    def __init__(
        self,
        # Data to pass to the Display
        label: str = "",
        description: str = "",
        collapsable: bool = False,
        collapsed: bool = False,
        # These constraints are added to the class defaults to create the two Constraints.
        extra_data_constraints: Sequence[Constraint] = (),
        extra_object_constraints: Sequence[Constraint] = (),
        serializer: Serializer[D, T] = None,
        deserializer: Deserializer[D, T] = None,
        key: str = "",
        children: Sequence[Keyed] = (),
    ):
        key, label = key_and_label(key, label)
        self.key = key
        self.serializer = serializer or self.default_serializer
        self.deserializer = deserializer or self.default_deserializer
        self.data_constraint = And(
            *self.default_data_constraints, *extra_data_constraints
        ).simplify()
        self.object_constraint = And(
            *self.default_object_constraints, *extra_object_constraints
        ).simplify()
        self.display_info = filter_display_info(
            {
                "type": "form",
                "label": label,
                "description": description,
                "collapsable": collapsable,
                "collapsed": collapsed,
            }
        )
        self.children = {child.key: child for child in children}

    def validate_data(self, data: JSONDict) -> ConstraintMap:
        child_constraints = {}
        for child, child_data in self.converter_to_sub_data(data).items():
            child_constraints[child.key] = child.validate_data(child_data)
        return super().validate_data(data) & ConstraintMap(
            child_constraints=child_constraints
        )

    def validate_object(self, obj: T) -> ConstraintMap:
        child_constraints = {}
        for child, child_data in self.converter_to_sub_object(obj).items():
            child_constraints[child.key] = child.validate_object(child_data)
        return super().validate_object(obj) & ConstraintMap(
            child_constraints=child_constraints
        )

    def deserialize(self, data: JSONDict) -> T:
        # Todo: build and raise ErrorMap
        data = {
            child.key: child.deserialize(sub_data)
            for child, sub_data in self.converter_to_sub_data(data).items()
        }
        return self.deserializer.deserialize(data)

    def serialize(self, obj: T) -> JSONDict:
        data: JSONDict = {}
        for child, sub_obj in self.converter_to_sub_object(obj):
            data[child.key] = child.serialize(sub_obj)
        return self.serializer.serialize(data)
