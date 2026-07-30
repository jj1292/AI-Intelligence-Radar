"""Run the observable minimal Radar Agent Harness."""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from agent.planner import DeterministicPlanner
from agent.state import RunState
from build_knowledge_base import (
    build_knowledge_base,
    deduplicate_signals,
    filter_signals_by_freshness,
)
from reporters.daily_briefing import write_daily_briefing
from reporters.subscription_feed import write_subscription_feeds
from runtime.event_log import JsonlTracer
from source_registry import load_source_registry
from tools.collection import CollectionBatch
from tools.anthropic_news import collect_anthropic_news
from tools.firecrawl_web import collect_firecrawl_web
from tools.github_releases import collect_github_releases
from tools.insight_analysis import analyze_signals
from tools.public_feeds import collect_public_feed
from tools.registry import ToolRegistry
from tools.source_dispatch import SourceDispatcher
from tools.x_twscrape import collect_x_posts


Collector = Callable[
    [dict[str, Any]],
    CollectionBatch | list[dict[str, Any]],
]


def build_source_dispatcher() -> SourceDispatcher:
    dispatcher = SourceDispatcher()
    dispatcher.register("anthropic_news", collect_anthropic_news)
    dispatcher.register("firecrawl", collect_firecrawl_web)
    dispatcher.register("atom", collect_github_releases)
    dispatcher.register("rss", collect_public_feed)
    dispatcher.register("x_twscrape", collect_x_posts)
    return dispatcher


def _select_sources(
    sources: list[dict[str, Any]],
    source_ids: set[str] | None = None,
    *,
    supported_modes: set[str] | None = None,
    include_requires_auth: bool = False,
    environment: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    modes = supported_modes or set(build_source_dispatcher().modes())
    if source_ids:
        selected = [
            source
            for source in sources
            if source["id"] in source_ids
            and source["collection_mode"] in modes
            and source["status"] in {"ready", "requires_auth"}
        ]
        missing = source_ids - {source["id"] for source in selected}
        if missing:
            raise ValueError(f"Unknown or unavailable sources: {sorted(missing)}")
        return selected
    selected: list[dict[str, Any]] = []
    for source in sources:
        if source["collection_mode"] not in modes:
            continue
        if source["status"] == "ready":
            selected.append(source)
            continue
        if source["status"] != "requires_auth" or not include_requires_auth:
            continue
        if environment is not None:
            names = source.get("selection_auth_env") or source.get("auth_env") or []
            values = [environment.get(str(name), "").strip() for name in names]
            if not values or any(value.lower() in {"", "0", "false", "no"} for value in values):
                continue
        selected.append(source)
    return selected


def run_radar_agent(
    sources: list[dict[str, Any]],
    output_dir: Path,
    *,
    as_of: datetime,
    max_age_hours: float = 48,
    objective: str = "Collect recent AI signals and build a traceable radar report.",
    collector: Collector | None = None,
    source_dispatcher: SourceDispatcher | None = None,
    feed_output_dir: Path | None = None,
    feed_max_items: int = 200,
    trace_path: Path | None = None,
    max_steps: int = 20,
) -> RunState:
    if as_of.tzinfo is None:
        raise ValueError("as_of must include a timezone offset.")

    source_map = {source["id"]: source for source in sources}
    state = RunState(
        objective=objective,
        as_of=as_of,
        max_age_hours=max_age_hours,
        pending_source_ids=list(source_map),
    )
    tracer = JsonlTracer(trace_path or output_dir / f"agent-trace-{state.run_id}.jsonl")
    planner = DeterministicPlanner()
    dispatcher = source_dispatcher or build_source_dispatcher()
    checkpoint_commits: list[Callable[[], None]] = []

    def collect_source(source_id: str) -> CollectionBatch:
        source = source_map[source_id]
        if collector is not None:
            result = collector(source)
            return result if isinstance(result, CollectionBatch) else CollectionBatch(result)
        return dispatcher.collect(source)

    def commit_checkpoints() -> int:
        for commit in checkpoint_commits:
            commit()
        return len(checkpoint_commits)

    registry = ToolRegistry()
    registry.register("collect_source", collect_source)
    registry.register(
        "filter_signals",
        lambda: deduplicate_signals(
            filter_signals_by_freshness(state.raw_signals, state.as_of, state.max_age_hours)
        ),
    )
    registry.register(
        "analyze_signals",
        lambda: analyze_signals(
            state.filtered_signals,
            existing_feed_path=(
                feed_output_dir / "feed.json" if feed_output_dir is not None else None
            ),
        ),
    )
    registry.register(
        "write_report",
        lambda: build_knowledge_base(
            state.filtered_signals,
            output_dir,
            state.as_of.date(),
            as_of=state.as_of,
            max_age_hours=state.max_age_hours,
        ),
    )
    registry.register(
        "write_briefing",
        lambda: write_daily_briefing(
            state.filtered_signals,
            output_dir,
            state.as_of.date(),
        ),
    )
    if feed_output_dir is not None:
        registry.register(
            "write_feed",
            lambda: write_subscription_feeds(
                state.filtered_signals,
                feed_output_dir,
                max_items=feed_max_items,
            ),
        )
    registry.register("commit_checkpoints", commit_checkpoints)

    state.status = "running"
    tracer.emit(state.run_id, "run_started", objective=objective, state=state.snapshot())

    while state.status == "running":
        if state.steps >= max_steps:
            state.status = "failed"
            state.stop_reason = "max_steps_exceeded"
            state.errors.append(f"Run exceeded max_steps={max_steps}.")
            break

        action = planner.next_action(state)
        state.steps += 1
        tracer.emit(
            state.run_id,
            "planner_decision",
            action=action.name,
            arguments=action.arguments,
            state=state.snapshot(),
        )
        if action.name == "stop":
            state.status = "completed"
            state.stop_reason = action.arguments["reason"]
            break

        state.tool_calls += 1
        tracer.emit(state.run_id, "tool_started", tool=action.name, arguments=action.arguments)
        try:
            observation = registry.call(action.name, **action.arguments)
        except Exception as exc:  # The trace must preserve source-level failures and continue safely.
            message = f"{action.name}: {exc}"
            state.errors.append(message)
            tracer.emit(state.run_id, "tool_failed", tool=action.name, error=message)
            if action.name == "collect_source":
                state.pending_source_ids.pop(0)
                if not state.pending_source_ids and state.successful_sources == 0:
                    state.status = "failed"
                    state.stop_reason = "all_sources_failed"
                    break
                continue
            state.status = "failed"
            state.stop_reason = "tool_failure"
            break

        if action.name == "collect_source":
            source_id = state.pending_source_ids.pop(0)
            state.successful_sources += 1
            state.raw_signals.extend(observation.signals)
            if observation.commit_checkpoint is not None:
                checkpoint_commits.append(observation.commit_checkpoint)
            observation_summary = {"source_id": source_id, "signals": len(observation.signals)}
        elif action.name == "filter_signals":
            state.filtered_signals = observation
            state.phase = "analyze"
            observation_summary = {
                "received": len(state.raw_signals),
                "selected": len(state.filtered_signals),
                "excluded": len(state.raw_signals) - len(state.filtered_signals),
            }
        elif action.name == "analyze_signals":
            state.filtered_signals = observation.signals
            state.result["analysis"] = {
                "analyzed": observation.analyzed,
                "reused": observation.reused,
                "skipped": observation.skipped,
                "errors": len(observation.errors),
            }
            state.errors.extend(observation.errors)
            state.phase = "write"
            observation_summary = state.result["analysis"]
        elif action.name == "write_report":
            state.result.update({
                "received": observation["received"],
                "fresh": observation["fresh"],
                "freshness_excluded": observation["freshness_excluded"],
                "written": observation["written"],
                "trend": str(observation["trend"]),
                "cards": [str(path) for path in observation["cards"]],
            })
            state.phase = "briefing"
            observation_summary = state.result
        elif action.name == "write_briefing":
            state.result["briefing"] = str(observation)
            state.phase = "feed" if feed_output_dir is not None else "checkpoint"
            observation_summary = {
                "briefing": str(observation),
                "signals": len(state.filtered_signals),
            }
        elif action.name == "write_feed":
            state.result["feed"] = {
                "rss": str(observation["rss"]),
                "json": str(observation["json"]),
                "items": observation["items"],
                "added": observation["added"],
            }
            state.phase = "checkpoint"
            observation_summary = state.result["feed"]
        elif action.name == "commit_checkpoints":
            state.result["checkpoints_committed"] = observation
            state.phase = "stop"
            state.stop_reason = "pipeline_complete"
            observation_summary = {"committed": observation}
        else:
            observation_summary = {"type": type(observation).__name__}

        tracer.emit(
            state.run_id,
            "tool_succeeded",
            tool=action.name,
            observation=observation_summary,
            state=state.snapshot(),
        )

    tracer.emit(
        state.run_id,
        "run_finished",
        state=state.snapshot(),
        result=state.result,
        errors=state.errors,
    )
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the minimal AI Intelligence Radar Agent Harness.")
    parser.add_argument("--config", type=Path, default=Path("config/subscriptions.json"))
    parser.add_argument("--output", type=Path, default=Path("outputs/latest-radar"))
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--feed-output", type=Path)
    parser.add_argument("--feed-max-items", type=int, default=200)
    parser.add_argument("--source", action="append", dest="source_ids")
    parser.add_argument(
        "--include-auth",
        action="store_true",
        help="Also run enabled sources that require publisher authentication.",
    )
    parser.add_argument("--hours", type=float, default=48)
    parser.add_argument("--as-of", default=datetime.now().astimezone().isoformat(timespec="seconds"))
    parser.add_argument(
        "--max-steps",
        type=int,
        help="Maximum Agent steps; defaults to the selected source count plus 9.",
    )
    args = parser.parse_args()

    all_sources = load_source_registry(args.config)
    dispatcher = build_source_dispatcher()
    sources = _select_sources(
        all_sources,
        set(args.source_ids) if args.source_ids else None,
        supported_modes=set(dispatcher.modes()),
        include_requires_auth=args.include_auth,
        environment=dict(os.environ),
    )
    if not sources:
        raise SystemExit("No runnable sources selected.")
    max_steps = args.max_steps if args.max_steps is not None else len(sources) + 9
    if max_steps <= 0:
        raise SystemExit("--max-steps must be greater than zero.")
    state = run_radar_agent(
        sources,
        args.output,
        as_of=datetime.fromisoformat(args.as_of.replace("Z", "+00:00")),
        max_age_hours=args.hours,
        source_dispatcher=dispatcher,
        feed_output_dir=args.feed_output,
        feed_max_items=args.feed_max_items,
        trace_path=args.trace,
        max_steps=max_steps,
    )
    print(
        f"run_id={state.run_id} status={state.status} "
        f"raw={len(state.raw_signals)} selected={len(state.filtered_signals)} "
        f"written={state.result.get('written', 0)} errors={len(state.errors)}"
    )
    if state.result.get("trend"):
        print(f"trend={state.result['trend']}")
    if state.result.get("briefing"):
        print(f"briefing={state.result['briefing']}")
    if state.result.get("feed"):
        print(f"feed={state.result['feed']['rss']}")
    for error in state.errors:
        print(f"error={error}")
    if state.status != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
