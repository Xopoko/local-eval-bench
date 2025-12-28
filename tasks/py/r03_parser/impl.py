"""Key-value parser for the refactor task.

Input format: "a=1; b=two; c=". Empty segments are ignored.
"""

from __future__ import annotations


def parse_pairs(line: str, sep: str = ";", kv: str = "=") -> dict[str, str]:
    result: dict[str, str] = {}
    if line is None:
        return result

    chunks = line.split(sep)
    for raw in chunks:
        part = raw.strip()
        if part == "":
            continue
        if kv in part:
            key, value = part.split(kv, 1)
        else:
            key, value = part, ""
        key = key.strip()
        value = value.strip()
        if key != "":
            result[key] = value
    return result
