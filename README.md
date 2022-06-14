[![Tests](https://github.com/travisjungroth/formlessness/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/travisjungroth/formlessness/actions/workflows/tests.yml)
[![CodeQL](https://github.com/travisjungroth/formlessness/actions/workflows/codeql-analysis.yml/badge.svg?branch=main)](https://github.com/travisjungroth/formlessness/actions/workflows/codeql-analysis.yml)
![License](https://img.shields.io/github/license/travisjungroth/formlessness?color=blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/travisjungroth/formlessness/branch/main/graph/badge.svg?token=2XR660JGGF)](https://codecov.io/gh/travisjungroth/formlessness)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/travisjungroth/formlessness/main.svg)](https://results.pre-commit.ci/latest/github/travisjungroth/formlessness/main)


# Formlessness

>Form is formlessness, formlessness is form.

--_The Heart Sutra_

Formlessness is a Python library for handling the backend work of web forms. It helps with serialization, validation and generating the form specification for the frontend.

## Motivations

 * Easier dynamic generation of everything form related.
 * Simple representation of complex validation logic.
 * High extendability.

## Example

<!--phmdoctest-share-names-->
```python
from pprint import pprint

from formlessness.forms import BasicForm
from formlessness.fields import IntField, StrField
from formlessness.constraints import GE

form = BasicForm(
    label='Person',
    children=[
        BasicForm(
            label='Name',
            children=[
                StrField(label='First Name'),
                StrField(label='Last Name'),
            ]
        ),
        IntField(label='Age', required=False, extra_data_constraints=[GE(0)])
    ],
)
pprint(form.display(), sort_dicts=False)
```
This is the form definition for the front end.
```
{'type': 'form',
 'label': 'Person',
 'collapsable': False,
 'collapsed': False,
 'objectPath': '',
 'contents': [{'type': 'form',
               'label': 'Name',
               'collapsable': False,
               'collapsed': False,
               'objectPath': '/name',
               'contents': [{'type': 'field',
                             'label': 'First Name',
                             'widget': {'type': 'text'},
                             'objectPath': '/name/first_name'},
                            {'type': 'field',
                             'label': 'Last Name',
                             'widget': {'type': 'text'},
                             'objectPath': '/name/last_name'}]},
              {'type': 'field',
               'label': 'Age',
               'widget': {'type': 'text'},
               'objectPath': '/age'}]}
```
A JSON Schema is automatically generated.
```python
pprint(form.data_schema(), sort_dicts=False)
```

```
{'type': 'object',
 'properties': {'name': {'type': 'object',
                         'properties': {'first_name': {'type': 'string'},
                                        'last_name': {'type': 'string'}},
                         'required': ['first_name', 'last_name'],
                         'unevaluatedProperties': False},
                'age': {'type': 'integer'}},
 'required': ['name'],
 'unevaluatedProperties': False,
 '$schema': 'http://json-schema.org/draft-07/schema#'}
```
## Development

### Poetry

#### Installing Poetry

If you're on MacOS with brew:

    brew install poetry

Otherwise, follow the [installation docs](https://python-poetry.org/docs/master/#installing-with-the-official-installer).

#### Installing Dev Dependencies

    poetry install

### Testing

    pytest

### Formatting

    pre-commit run -a

### Run docs locally

    mkdocs serve

---
Formlessness is not an official Netflix project.
