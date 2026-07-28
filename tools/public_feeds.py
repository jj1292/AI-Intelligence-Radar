"""Collect normalized intelligence signals from public RSS and Atom feeds."""

from __future__ import annotations

import html
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
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


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, *names: str) -> str:
    for child in element:
        if _local_name(child.tag) in names and child.text:
            return child.text.strip()
    return ""


def _atom_link(entry: ET.Element) -> str:
    for link in entry.findall(f"{ATOM}link"):
        if link.get("rel", "alternate") == "alternate" and link.get("href"):
            return link.get("href", "").strip()
    return ""


def _rss_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value
    return parsed.isoformat()


def _signal(
    source: dict[str, Any],
    *,
    title: str,
    link: str,
    published_at: str,
    content: str,
) -> dict[str, Any] | None:
    if not link or not published_at:
        return None
    summary = _plain_text(content) or f"{source['name']} 发布了新内容。"
    is_reddit = source.get("channel") == "reddit"
    platform = "reddit" if is_reddit else ("official" if source["source_tier"] == 1 else "other")
    return {
        "title": f"{source['name']} · {title or 'Untitled update'}",
        "canonical_url": link,
        "source_name": source["name"],
        "source_tier": source["source_tier"],
        "platform": platform,
        "company": source["company"],
        "published_at": published_at,
        "summary": summary,
        "why_it_matters": (
            "这是社区早期信号，只用于发现问题、用例和情绪；重要事实需要回到 T1 官方来源核验。"
            if is_reddit
            else "这是可直接订阅的一手更新，可用于观察产品、研究和行业变化。"
        ),
        "evidence": [summary[:240]],
        "topics": list(source["topics"]),
        "impact_score": 2 if is_reddit else 3,
        "confidence": 0.65 if is_reddit else 0.9,
    }


def parse_public_feed(xml_text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    signals: list[dict[str, Any]] = []
    if _local_name(root.tag) == "feed":
        for entry in root.findall(f"{ATOM}entry"):
            signal = _signal(
                source,
                title=_child_text(entry, "title"),
                link=_atom_link(entry),
                published_at=_child_text(entry, "published", "updated"),
                content=_child_text(entry, "content", "summary"),
            )
            if signal is not None:
                signals.append(signal)
        return signals

    channel = next((child for child in root if _local_name(child.tag) == "channel"), None)
    if channel is None:
        raise ValueError(f"Unsupported RSS/Atom document for {source.get('id')}.")
    for item in channel:
        if _local_name(item.tag) != "item":
            continue
        signal = _signal(
            source,
            title=_child_text(item, "title"),
            link=_child_text(item, "link"),
            published_at=_rss_timestamp(_child_text(item, "pubDate", "date", "updated")),
            content=_child_text(item, "description", "encoded", "summary"),
        )
        if signal is not None:
            signals.append(signal)
    return signals


def fetch_public_feed(url: str, timeout: float = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
            "User-Agent": (
                "AI-Intelligence-Radar/0.7 "
                "(+https://github.com/jj1292/AI-Intelligence-Radar)"
            ),
        },
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read().decode("utf-8")


def collect_public_feed(
    source: dict[str, Any],
    *,
    fetcher: Callable[[str], str] = fetch_public_feed,
) -> list[dict[str, Any]]:
    if source.get("collection_mode") != "rss":
        raise ValueError(f"Source {source.get('id')} is not a public RSS/Atom source.")
    return parse_public_feed(fetcher(source["url"]), source)
