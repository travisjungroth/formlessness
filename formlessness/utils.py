from typing import Iterable


def key_and_label(key: str, label: str) -> tuple[str, str]:
    """
    If one of key or label is missing, generate it from the other.

    >>> key_and_label("foo_bar", "Foo Bar")
    ('foo_bar', 'Foo Bar')
    >>> key_and_label("foo_bar", "")
    ('foo_bar', 'Foo Bar')
    >>> key_and_label("", "Foo Bar")
    ('foo_bar', 'Foo Bar')
    >>> key_and_label("", "Foo Bar!")
    ('foo_bar', 'Foo Bar!')
    """
    if key and label:
        return key, label
    if key:
        return key, key.replace("_", " ").title()
    if label:
        key = "".join(
            [c for c in label.lower().replace(" ", "_") if c.isalnum() or c == "_"]
        )
        return key, label
    raise ValueError("Must set key or label.")
