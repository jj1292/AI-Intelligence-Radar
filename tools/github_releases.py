"""Collect normalized intelligence signals from GitHub Release Atom feeds."""

from __future__ import annotations

import html
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any, Callable

import certifi


ATOM = "{http://www.w3.org/2005/Atom}"


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def _plain_text(value: str, limit: int = 400) -> str:
    extractor = _HTMLTextExtractor()
    extractor.feed(html.unescape(value))
    text = re.sub(r"\s+", " ", " ".join(extractor.parts)).strip()
    return text[:limit].rstrip()


def parse_github_releases_atom(xml_text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    signals: list[dict[str, Any]] = []
    for entry in root.findall(f"{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "Untitled release").strip()
        published_at = (
            entry.findtext(f"{ATOM}published")
            or entry.findtext(f"{ATOM}updated")
            or ""
        ).strip()
        link = next(
            (
                element.get("href", "")
                for element in entry.findall(f"{ATOM}link")
                if element.get("rel") == "alternate"
            ),
            "",
        )
        content = entry.findtext(f"{ATOM}content") or entry.findtext(f"{ATOM}summary") or ""
        summary = _plain_text(content) or f"{source['name']} 发布 {title}。"
        if not link or not published_at:
            continue
        signals.append(
            {
                "title": f"{source['company']} · {title}",
                "canonical_url": link,
                "source_name": source["name"],
                "source_tier": source["source_tier"],
                "platform": "github",
                "company": source["company"],
                "published_at": published_at,
                "summary": summary,
                "why_it_matters": (
                    "这是官方代码仓库发布信号，可用于观察产品迭代速度、能力变化和可靠性改进。"
                ),
                "evidence": [summary[:240]],
                "topics": list(source["topics"]),
                "impact_score": 3,
                "confidence": 0.98,
            }
        )
    return signals


def fetch_atom(url: str, timeout: float = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AI-Intelligence-Radar/0.4 (+https://github.com/jj1292/AI-Intelligence-Radar)"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read().decode("utf-8")


def collect_github_releases(
    source: dict[str, Any],
    *,
    fetcher: Callable[[str], str] = fetch_atom,
) -> list[dict[str, Any]]:
    if source.get("collection_mode") != "atom":
        raise ValueError(f"Source {source.get('id')} is not an Atom source.")
    return parse_github_releases_atom(fetcher(source["url"]), source)
