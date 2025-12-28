"""Tiny LRU cache for the refactor task.

The logic is intentionally compact. Refactor for clarity and add tests.
"""

from __future__ import annotations

from typing import Any


class TinyLRU:
    def __init__(self, maxsize: int = 4) -> None:
        self.maxsize = maxsize
        self._data: dict[Any, Any] = {}
        self._order: list[Any] = []  # oldest first

    def get(self, key: Any, default: Any = None) -> Any:
        if key in self._data:
            if key in self._order:
                self._order.remove(key)
            self._order.append(key)
            return self._data[key]
        return default

    def set(self, key: Any, value: Any) -> None:
        if key in self._data:
            self._data[key] = value
            if key in self._order:
                self._order.remove(key)
            self._order.append(key)
            return

        self._data[key] = value
        self._order.append(key)
        if self.maxsize is not None and self.maxsize > 0:
            while len(self._order) > self.maxsize:
                old = self._order.pop(0)
                if old in self._data:
                    del self._data[old]

    def __len__(self) -> int:
        return len(self._data)
