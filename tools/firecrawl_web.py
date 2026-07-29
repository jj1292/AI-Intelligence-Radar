"""Collect structured official blog/news signals through Firecrawl v2."""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.parse import urljoin

import certifi


DEFAULT_API_URL = "https://api.firecrawl.dev/v2/scrape"

ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "published_at": {"type": "string"},
                    "summary": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["title", "url", "published_at", "summary"],
            },
        }
    },
    "required": ["articles"],
}


def _normalize_date(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("empty publication date")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            parsed = datetime.strptime(text, "%Y-%m-%d")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def parse_firecrawl_response(
    payload: dict[str, Any],
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    if payload.get("success") is not True:
        raise ValueError(f"Firecrawl scrape failed: {payload.get('error', 'unknown error')}")
    data = payload.get("data")
    extracted = data.get("json") if isinstance(data, dict) else None
    articles = extracted.get("articles") if isinstance(extracted, dict) else None
    if not isinstance(articles, list):
        raise ValueError("Firecrawl response is missing data.json.articles.")

    max_results = source.get("max_results", 30)
    signals: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title") or "").strip()
        raw_url = str(article.get("url") or "").strip()
        summary = str(article.get("summary") or "").strip()
        published_at = str(article.get("published_at") or "").strip()
        if not title or not raw_url or not summary or not published_at:
            continue
        canonical_url = urljoin(source["url"], raw_url)
        if not canonical_url.startswith(("https://", "http://")) or canonical_url in seen_urls:
            continue
        try:
            normalized_date = _normalize_date(published_at)
        except ValueError:
            continue
        seen_urls.add(canonical_url)
        category = str(article.get("category") or "Official news").strip()
        signals.append(
            {
                "title": f"{source['company']} · {title}",
                "canonical_url": canonical_url,
                "source_name": source["name"],
                "source_tier": source["source_tier"],
                "platform": "official",
                "company": source["company"],
                "published_at": normalized_date,
                "summary": summary[:400].rstrip(),
                "why_it_matters": (
                    f"这是 {source['company']} 官方网站的一手更新，"
                    f"可用于跟踪 {category} 方向的产品、研究或公司变化。"
                ),
                "evidence": [summary[:240].rstrip()],
                "topics": list(source["topics"]),
                "impact_score": 3,
                "confidence": 0.9,
            }
        )
        if len(signals) >= max_results:
            break
    return signals


def fetch_firecrawl(
    source: dict[str, Any],
    *,
    timeout: float = 120,
) -> dict[str, Any]:
    api_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not configured.")
    api_url = os.environ.get("FIRECRAWL_API_URL", DEFAULT_API_URL).strip()
    body = json.dumps(
        {
            "url": source["url"],
            "formats": [
                {
                    "type": "json",
                    "schema": ARTICLE_SCHEMA,
                    "prompt": (
                        "Extract the newest official news or blog article cards. "
                        "Return only real article pages, newest first."
                    ),
                }
            ],
            "onlyMainContent": True,
            "timeout": int(timeout * 1000),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": (
                "AI-Intelligence-Radar/0.8 "
                "(+https://github.com/jj1292/AI-Intelligence-Radar)"
            ),
        },
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=timeout + 10, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def collect_firecrawl_web(
    source: dict[str, Any],
    *,
    fetcher: Callable[[dict[str, Any]], dict[str, Any]] = fetch_firecrawl,
) -> list[dict[str, Any]]:
    if source.get("collection_mode") != "firecrawl":
        raise ValueError(f"Source {source.get('id')} is not a Firecrawl source.")
    return parse_firecrawl_response(fetcher(source), source)
