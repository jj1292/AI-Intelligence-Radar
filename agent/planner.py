"""Deterministic baseline planner that makes Loop decisions observable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent.state import RunState


@dataclass(frozen=True)
class Action:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


class DeterministicPlanner:
    """A replaceable baseline; a model planner can implement the same contract later."""

    def next_action(self, state: RunState) -> Action:
        if state.phase == "collect" and state.pending_source_ids:
            return Action("collect_source", {"source_id": state.pending_source_ids[0]})
        if state.phase == "collect":
            return Action("filter_signals")
        if state.phase == "write":
            return Action("write_report")
        return Action("stop", {"reason": state.stop_reason or "pipeline_complete"})
