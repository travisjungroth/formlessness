from __future__ import annotations

from functools import partial

import jsonschema

validate_json = partial(
    jsonschema.validate, format_checker=jsonschema.draft7_format_checker
)
