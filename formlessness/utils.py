def key_and_label(key: str, label: str) -> tuple[str, str]:
    if key and label:
        return key, label
    if key:
        return key, key
    if label:
        key = "".join(
            [c for c in label.lower().replace(" ", "_") if c.isalnum() or c == "_"]
        )
        return key, label
    raise ValueError("Must set key or label.")
