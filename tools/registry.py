"""Minimal typed tool registry for the Radar Agent loop."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, tool: Callable[..., Any]) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = tool

    def call(self, name: str, **arguments: Any) -> Any:
        try:
            tool = self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc
        return tool(**arguments)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
