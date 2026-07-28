"""Collect official Anthropic Newsroom posts without a third-party feed."""

from __future__ import annotations

import html
import re
import ssl
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urljoin

import certifi


DATE_PATTERN = re.compile(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}$")


class _AnthropicNewsParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.items: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None
        self.depth = 0
        self.context: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        href = attributes.get("href") or ""
        if self.current is None and tag == "a" and href.startswith("/news/"):
            self.current = {
                "url": urljoin(self.base_url, href),
                "title": "",
                "published_at": "",
                "category": "",
                "summary": "",
            }
            self.depth = 1
            self.context = [(tag, attributes.get("class") or "")]
            return
        if self.current is not None:
            self.depth += 1
            self.context.append((tag, attributes.get("class") or ""))

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        self.depth -= 1
        if self.context:
            self.context.pop()
        if self.depth == 0:
            if self.current["title"] and self.current["published_at"]:
                self.items.append(self.current)
            self.current = None
            self.context = []

    def handle_data(self, data: str) -> None:
        if self.current is None or not self.context:
            return
        text = re.sub(r"\s+", " ", html.unescape(data)).strip()
        if not text:
            return
        tag, class_name = self.context[-1]
        class_lower = class_name.lower()
        if tag == "time" or DATE_PATTERN.fullmatch(text):
            self.current["published_at"] = text
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} or "title" in class_lower:
            self.current["title"] = f"{self.current['title']} {text}".strip()
        elif tag == "p" and "body" in class_lower:
            self.current["summary"] = f"{self.current['summary']} {text}".strip()
        elif "subject" in class_lower:
            self.current["category"] = text


def _published_at(value: str) -> str:
    parsed = datetime.strptime(value, "%b %d, %Y")
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def parse_anthropic_news(
    html_text: str,
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    parser = _AnthropicNewsParser(source["url"])
    parser.feed(html_text)
    unique: dict[str, dict[str, str]] = {}
    for item in parser.items:
        existing = unique.get(item["url"])
        if existing is None or (item["summary"] and not existing["summary"]):
            unique[item["url"]] = item

    max_results = source.get("max_results", 30)
    if not isinstance(max_results, int) or not 1 <= max_results <= 100:
        raise ValueError("Anthropic News max_results must be between 1 and 100.")

    signals: list[dict[str, Any]] = []
    for item in list(unique.values())[:max_results]:
        category = item["category"] or "Official news"
        summary = item["summary"] or (
            f"Anthropic Newsroom 发布：{item['title']}（{category}）。"
        )
        signals.append(
            {
                "title": f"Anthropic · {item['title']}",
                "canonical_url": item["url"],
                "source_name": source["name"],
                "source_tier": 1,
                "platform": "official",
                "company": "Anthropic",
                "published_at": _published_at(item["published_at"]),
                "summary": summary[:400].rstrip(),
                "why_it_matters": (
                    "这是 Anthropic 官方博客的一手信息，可用于跟踪 Claude 产品、研究、"
                    "安全与公司动态。"
                ),
                "evidence": [summary[:240].rstrip()],
                "topics": list(source["topics"]),
                "impact_score": 3,
                "confidence": 0.98,
            }
        )
    return signals


def fetch_anthropic_news(url: str, timeout: float = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html",
            "User-Agent": (
                "AI-Intelligence-Radar/0.7 "
                "(+https://github.com/jj1292/AI-Intelligence-Radar)"
            ),
        },
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read().decode("utf-8")


def collect_anthropic_news(
    source: dict[str, Any],
    *,
    fetcher: Callable[[str], str] = fetch_anthropic_news,
) -> list[dict[str, Any]]:
    if source.get("collection_mode") != "anthropic_news":
        raise ValueError(f"Source {source.get('id')} is not an Anthropic News source.")
    return parse_anthropic_news(fetcher(source["url"]), source)
