[![Tests](https://github.com/travisjungroth/formlessness/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/travisjungroth/formlessness/actions/workflows/tests.yml)
![License](https://img.shields.io/github/license/travisjungroth/formlessness?color=blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/travisjungroth/formlessness/branch/main/graph/badge.svg?token=2XR660JGGF)](https://codecov.io/gh/travisjungroth/formlessness)

# Formlessness

>Form is formlessness, formlessness is form.

--_The Heart Sutra_

Formlessness is a Python library for handling the backend work of web forms. It helps with serialization, validation and generating the form specification for the frontend.

## Motivations

 * Easier dynamic generation of everything form related.
 * Simple representation of complex validation logic.
 * High extendability.

## Development

### Poetry

#### Installing Poetry

If you're on MacOS with brew:

    brew install poetry

Otherwise, follow the [installation docs](https://python-poetry.org/docs/master/#installing-with-the-official-installer).

#### Installing Dev Dependencies

    poetry install

### Testing
To run the same tests as the CI:

    doit test

For anything custom, use `pytest`.

### Formatting

    doit format

### Run docs locally

    mkdocs serve
