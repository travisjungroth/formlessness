from abc import ABC
from collections.abc import Sequence
from typing import Optional
from typing import Union

from formlessness.base_classes import Converter
from formlessness.base_classes import Keyed
from formlessness.base_classes import Parent
from formlessness.constraints import And
from formlessness.constraints import Constraint
from formlessness.constraints import ConstraintMap
from formlessness.constraints import HasKeys
from formlessness.constraints import is_null
from formlessness.constraints import not_null
from formlessness.deserializers import Deserializer
from formlessness.exceptions import DeserializationError
from formlessness.exceptions import FormErrors
from formlessness.new_forms import FixedMappingForm
from formlessness.serializers import Serializer
from formlessness.types import D
from formlessness.types import JSONDict
from formlessness.types import T
from formlessness.utils import MISSING
from formlessness.utils import key_and_label
from formlessness.utils import remove_null_values


class Form(Parent, Converter[D, T], ABC):
    """
    Fields serialize objects, deserialize data, and generate their own Display.

    They are different from Fields in that they're Parents i.e. they can contain Field, Forms and Sections.
    This abstract class exists for type checking and if you want to deviate from the implementation of BasicForm.
    """


class BasicForm(FixedMappingForm):
    pass







