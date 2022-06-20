from abc import ABC

from formlessness.base_classes import Converter
from formlessness.base_classes import Parent
from formlessness.new_forms import FixedMappingForm
from formlessness.types import D
from formlessness.types import T


class Form(Parent, Converter[D, T], ABC):
    """
    Fields serialize objects, deserialize data, and generate their own Display.

    They are different from Fields in that they're Parents i.e. they can contain Field, Forms and Sections.
    This abstract class exists for type checking and if you want to deviate from the implementation of BasicForm.
    """


class BasicForm(FixedMappingForm):
    pass
