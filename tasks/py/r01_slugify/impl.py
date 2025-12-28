"""Slugify utility for the refactor task.

The current implementation works but is intentionally compact and uses repeated
string operations. Refactor for readability and add tests.
"""

from __future__ import annotations

import re


def slugify(text: object, max_len: int = 50) -> str:
    if text is None:
        return ""

    s = str(text).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")

    if max_len is None or max_len <= 0:
        return s
    if len(s) <= max_len:
        return s

    cut = s[:max_len]
    if "-" in cut:
        cut = cut.rsplit("-", 1)[0]
    return cut.strip("-")
