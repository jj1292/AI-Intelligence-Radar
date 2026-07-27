"""Dispatch source configurations to collection-mode-specific adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tools.collection import CollectionBatch


Collector = Callable[
    [dict[str, Any]],
    CollectionBatch | list[dict[str, Any]],
]


class SourceDispatcher:
    def __init__(self) -> None:
        self._collectors: dict[str, Collector] = {}

    def register(self, collection_mode: str, collector: Collector) -> None:
        if collection_mode in self._collectors:
            raise ValueError(f"Collector already registered: {collection_mode}")
        self._collectors[collection_mode] = collector

    def collect(self, source: dict[str, Any]) -> CollectionBatch:
        collection_mode = source.get("collection_mode", "")
        try:
            collector = self._collectors[collection_mode]
        except KeyError as exc:
            raise ValueError(f"Unsupported collection mode: {collection_mode}") from exc
        result = collector(source)
        return result if isinstance(result, CollectionBatch) else CollectionBatch(result)

    def modes(self) -> tuple[str, ...]:
        return tuple(sorted(self._collectors))

