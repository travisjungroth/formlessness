def key_and_label(key: str, label: str) -> tuple[str, str]:
    if key and label:
        return key, label
    if key:
        return key, key
    if label:
        return "".join([c for c in label.lower() if c.isalnum()]), key
    raise ValueError("Must set key or label.")
