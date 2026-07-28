"""Load, expand, validate, and summarize AI Intelligence Radar sources."""

from __future__ import annotations

import argparse
import json
import re
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
SUBSCRIPTION_KEYS = {
    "$schema",
    "version",
    "github_releases",
    "official_web",
    "rss_feeds",
    "reddit",
    "x",
}
GITHUB_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REDDIT_COMMUNITY_PATTERN = re.compile(r"^[A-Za-z0-9_]{2,21}$")
X_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,15}$")


def load_source_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        sources = payload
    elif isinstance(payload, dict):
        sources = expand_subscriptions(payload)
    else:
        raise ValueError("Source config must be a JSON array or subscription object.")
    validate_sources(sources)
    return sources


def _require_list(config: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = config.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a JSON array.")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Every {key} entry must be an object.")
    return value


def _enabled(item: dict[str, Any]) -> bool:
    enabled = item.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be true or false.")
    return enabled


def _topics(item: dict[str, Any], default: list[str]) -> list[str]:
    topics = item.get("topics", default)
    if not isinstance(topics, list) or not topics:
        raise ValueError("topics must be a non-empty JSON array.")
    if not all(isinstance(topic, str) and topic.strip() for topic in topics):
        raise ValueError("Every topic must be a non-empty string.")
    return [topic.strip() for topic in topics]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "source"


def _required_text(item: dict[str, Any], key: str, label: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} requires a non-empty {key}.")
    return value.strip()


def expand_subscriptions(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand the human-editable subscription file into runnable source records."""

    unknown = sorted(set(config) - SUBSCRIPTION_KEYS)
    if unknown:
        raise ValueError(f"Unknown subscription sections: {unknown}")
    if config.get("version", 1) != 1:
        raise ValueError("Unsupported subscription config version.")

    sources: list[dict[str, Any]] = []
    for item in _require_list(config, "github_releases"):
        if not _enabled(item):
            continue
        repository = _required_text(item, "repo", "GitHub release subscription")
        if not GITHUB_REPOSITORY_PATTERN.fullmatch(repository):
            raise ValueError(f"Invalid GitHub repository: {repository}")
        owner = repository.split("/", 1)[0]
        company = str(item.get("company") or owner).strip()
        sources.append(
            {
                "id": f"github_{_slug(repository)}_releases",
                "name": str(item.get("name") or f"{repository} releases").strip(),
                "company": company,
                "source_tier": 1,
                "channel": "official_repository",
                "collection_mode": "atom",
                "url": f"https://github.com/{repository}/releases.atom",
                "status": "ready",
                "topics": _topics(item, ["releases"]),
            }
        )

    for item in _require_list(config, "official_web"):
        if not _enabled(item):
            continue
        adapter = _required_text(item, "adapter", "Official web subscription")
        if adapter not in {"anthropic_news"}:
            raise ValueError(f"Unsupported official web adapter: {adapter}")
        name = _required_text(item, "name", "Official web subscription")
        url = _required_text(item, "url", "Official web subscription")
        if not url.startswith("https://"):
            raise ValueError(f"Official web URL must start with https://: {url}")
        max_results = item.get("max_results", 30)
        if not isinstance(max_results, int) or not 1 <= max_results <= 100:
            raise ValueError(f"Official web max_results must be between 1 and 100: {name}")
        sources.append(
            {
                "id": str(item.get("id") or f"web_{_slug(name)}").strip(),
                "name": name,
                "company": str(item.get("company") or name).strip(),
                "source_tier": 1,
                "channel": "official_newsroom",
                "collection_mode": adapter,
                "url": url,
                "status": "ready",
                "max_results": max_results,
                "topics": _topics(item, ["products", "research", "company"]),
            }
        )

    for item in _require_list(config, "rss_feeds"):
        if not _enabled(item):
            continue
        name = _required_text(item, "name", "RSS subscription")
        url = _required_text(item, "url", "RSS subscription")
        if not url.startswith(("https://", "http://")):
            raise ValueError(f"RSS URL must start with http:// or https://: {url}")
        source_tier = item.get("source_tier", 1)
        if source_tier not in {1, 2, 3}:
            raise ValueError(f"Invalid RSS source_tier for {name}")
        sources.append(
            {
                "id": str(item.get("id") or f"rss_{_slug(name)}").strip(),
                "name": name,
                "company": str(item.get("company") or name).strip(),
                "source_tier": source_tier,
                "channel": str(item.get("channel") or "official").strip(),
                "collection_mode": "rss",
                "url": url,
                "status": "ready",
                "topics": _topics(item, ["updates"]),
            }
        )

    reddit_config = config.get("reddit", {})
    if not isinstance(reddit_config, dict):
        raise ValueError("reddit must be a JSON object.")
    if _enabled(reddit_config):
        communities = reddit_config.get("communities", [])
        if not isinstance(communities, list):
            raise ValueError("reddit communities must be a JSON array.")
        normalized_communities: list[str] = []
        for value in communities:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Every Reddit community must be a non-empty string.")
            community = value.strip()
            if community.lower().startswith("r/"):
                community = community[2:]
            if not REDDIT_COMMUNITY_PATTERN.fullmatch(community):
                raise ValueError(f"Invalid Reddit community: {community}")
            normalized_communities.append(community)
        limit = reddit_config.get("max_results", 25)
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Reddit max_results must be between 1 and 100.")
        if normalized_communities:
            joined_communities = "+".join(normalized_communities)
            sources.append(
                {
                    "id": "reddit_selected_communities",
                    "name": "Selected Reddit communities",
                    "company": "Community",
                    "source_tier": 3,
                    "channel": "reddit",
                    "collection_mode": "rss",
                    "url": (
                        f"https://www.reddit.com/r/{joined_communities}/new/.rss"
                        f"?limit={limit}"
                    ),
                    "status": "ready",
                    "topics": _topics(
                        reddit_config,
                        ["community-feedback", "use-cases", "emerging-signals"],
                    ),
                    "targets": normalized_communities,
                }
            )

    x_config = config.get("x", {})
    if not isinstance(x_config, dict):
        raise ValueError("x must be a JSON object.")
    if _enabled(x_config):
        accounts = _require_list(x_config, "accounts")
        enabled_accounts = [item for item in accounts if _enabled(item)]
        if enabled_accounts:
            usernames: list[str] = []
            author_companies: dict[str, str] = {}
            for item in enabled_accounts:
                username = _required_text(item, "username", "X subscription").lstrip("@")
                if not X_USERNAME_PATTERN.fullmatch(username):
                    raise ValueError(f"Invalid X username: {username}")
                usernames.append(username)
                author_companies[username] = str(item.get("company") or username).strip()
            max_results = x_config.get("max_results", 100)
            if not isinstance(max_results, int) or not 1 <= max_results <= 500:
                raise ValueError("X max_results must be between 1 and 500.")
            filters = []
            if not x_config.get("include_retweets", False):
                filters.append("-is:retweet")
            if not x_config.get("include_replies", False):
                filters.append("-is:reply")
            if x_config.get("require_links", True):
                filters.append("has:links")
            from_query = " OR ".join(f"from:{username}" for username in usernames)
            sources.append(
                {
                    "id": "x_selected_accounts",
                    "name": "Selected AI accounts on X",
                    "company": "Multiple",
                    "source_tier": 2,
                    "channel": "x",
                    "collection_mode": "x_twscrape",
                    "url": "https://x.com/search",
                    "status": "requires_auth",
                    "auth_env": ["X_TWSCRAPE_DB"],
                    "publisher_auth_env": [
                        "X_ACCOUNT_USERNAME",
                        "X_COOKIE_AUTH_TOKEN",
                        "X_COOKIE_CT0",
                    ],
                    "query": f"({from_query}) {' '.join(filters)}".strip(),
                    "max_results": max_results,
                    "author_companies": author_companies,
                    "topics": _topics(
                        x_config,
                        ["models", "agents", "research", "products"],
                    ),
                    "notes": (
                        "One maintainer account collects for the public feeds; "
                        "subscribers never provide credentials."
                    ),
                }
            )
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
    parser.add_argument("--config", type=Path, default=Path("config/subscriptions.json"))
    args = parser.parse_args()
    print(summarize_sources(load_source_registry(args.config)))


if __name__ == "__main__":
    main()
