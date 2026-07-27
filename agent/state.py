"""Run state for the minimal Radar Agent loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class RunState:
    objective: str
    as_of: datetime
    max_age_hours: float
    pending_source_ids: list[str]
    run_id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "created"
    phase: str = "collect"
    steps: int = 0
    tool_calls: int = 0
    successful_sources: int = 0
    raw_signals: list[dict[str, Any]] = field(default_factory=list)
    filtered_signals: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    stop_reason: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "phase": self.phase,
            "steps": self.steps,
            "tool_calls": self.tool_calls,
            "successful_sources": self.successful_sources,
            "pending_sources": len(self.pending_source_ids),
            "raw_signals": len(self.raw_signals),
            "filtered_signals": len(self.filtered_signals),
            "errors": len(self.errors),
            "stop_reason": self.stop_reason,
        }
