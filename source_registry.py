"""Validate and summarize the AI Intelligence Radar source registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "name",
    "company",
    "source_tier",
    "channel",
    "collection_mode",
    "url",
    "status",
    "topics",
}
ALLOWED_STATUSES = {"ready", "adapter_required", "requires_auth", "disabled"}


def load_source_registry(path: Path) -> list[dict[str, Any]]:
    sources = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(sources, list):
        raise ValueError("Source registry must be a JSON array.")
    validate_sources(sources)
    return sources


def validate_sources(sources: list[dict[str, Any]]) -> None:
    seen_ids: set[str] = set()
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ValueError(f"Source {index} must be an object.")
        missing = sorted(REQUIRED_FIELDS - set(source))
        if missing:
            raise ValueError(f"Source {index} missing fields: {missing}")
        if source["id"] in seen_ids:
            raise ValueError(f"Duplicate source id: {source['id']}")
        if source["source_tier"] not in {1, 2, 3}:
            raise ValueError(f"Invalid source tier for {source['id']}")
        if source["status"] not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status for {source['id']}")
        if source["status"] == "requires_auth" and not source.get("auth_env"):
            raise ValueError(f"Missing auth_env for {source['id']}")
        seen_ids.add(source["id"])


def summarize_sources(sources: list[dict[str, Any]]) -> str:
    ready = sum(source["status"] == "ready" for source in sources)
    adapter_required = sum(source["status"] == "adapter_required" for source in sources)
    gated = sum(source["status"] == "requires_auth" for source in sources)
    tiers = {tier: sum(source["source_tier"] == tier for source in sources) for tier in (1, 2, 3)}
    return (
        f"sources={len(sources)} ready={ready} adapter_required={adapter_required} requires_auth={gated} "
        f"tier1={tiers[1]} tier2={tiers[2]} tier3={tiers[3]}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AI Radar source registry.")
    parser.add_argument("--config", type=Path, default=Path("config/sources.json"))
    args = parser.parse_args()
    print(summarize_sources(load_source_registry(args.config)))


if __name__ == "__main__":
    main()
