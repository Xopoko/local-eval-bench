"""Basic stats helper for the refactor task.

The function works but is intentionally written as one long block. Refactor into
small helpers and add tests for edge cases.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable


def basic_stats(values: Iterable[float]) -> dict[str, float | int | None | list[float]]:
    if values is None:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "mode": None,
        }

    data = list(values)
    if len(data) == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "mode": None,
        }

    data.sort()
    total = 0.0
    for x in data:
        total += float(x)
    mean = total / len(data)

    if len(data) % 2 == 1:
        median = float(data[len(data) // 2])
    else:
        mid = len(data) // 2
        median = (float(data[mid - 1]) + float(data[mid])) / 2.0

    counts = Counter(data)
    max_count = max(counts.values())
    if max_count == 1:
        mode = []
    else:
        mode = [float(k) for k, v in counts.items() if v == max_count]

    return {
        "count": len(data),
        "min": float(data[0]),
        "max": float(data[-1]),
        "mean": mean,
        "median": median,
        "mode": mode,
    }
