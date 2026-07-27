"""Shared collection result contract for source adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class CollectionBatch:
    """Signals plus an optional checkpoint commit deferred until the run succeeds."""

    signals: list[dict[str, Any]]
    commit_checkpoint: Callable[[], None] | None = None

