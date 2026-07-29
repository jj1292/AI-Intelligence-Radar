"""Publish normalized Radar signals as rolling RSS and JSON feeds."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any, Iterable

from build_knowledge_base import load_signals, parse_published_at


DEFAULT_HOME_URL = "https://github.com/jj1292/AI-Intelligence-Radar"
DEFAULT_FEED_BASE_URL = "https://jj1292.github.io/AI-Intelligence-Radar"
JSON_FEED_VERSION = "https://jsonfeed.org/version/1.1"
ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"


def _load_existing_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError(f"Invalid JSON feed history: {path}")
    return items


def _signal_to_item(signal: dict[str, Any]) -> dict[str, Any]:
    published_at = parse_published_at(signal["published_at"])
    author = signal.get("author") or signal["company"]
    return {
        "id": signal["canonical_url"],
        "url": signal["canonical_url"],
        "title": signal["title"],
        "content_text": (
            f"{signal['summary']}\n\nWhy it matters: {signal['why_it_matters']}\n\n"
            f"Source: {signal['source_name']} (T{signal['source_tier']})"
        ),
        "date_published": published_at.isoformat(),
        "authors": [{"name": str(author)}],
        "tags": [*signal["topics"], f"T{signal['source_tier']}", signal["platform"]],
        "_radar": {
            "company": signal["company"],
            "source_name": signal["source_name"],
            "source_tier": signal["source_tier"],
            "platform": signal["platform"],
            "impact_score": signal["impact_score"],
            "confidence": signal["confidence"],
            "evidence": list(signal.get("evidence", [])),
        },
    }


def _item_timestamp(item: dict[str, Any]) -> float:
    value = item.get("date_published")
    if not isinstance(value, str):
        raise ValueError("Feed item is missing date_published.")
    return parse_published_at(value).timestamp()


def merge_feed_items(
    existing_items: Iterable[dict[str, Any]],
    signals: Iterable[dict[str, Any]],
    *,
    max_items: int = 200,
) -> tuple[list[dict[str, Any]], int]:
    if max_items < 1:
        raise ValueError("max_items must be greater than zero.")
    merged: dict[str, dict[str, Any]] = {}
    for item in existing_items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("Feed item is missing a valid id.")
        _item_timestamp(item)
        merged[item_id] = item

    existing_ids = set(merged)
    for signal in signals:
        item = _signal_to_item(signal)
        merged[item["id"]] = item

    ordered = sorted(merged.values(), key=_item_timestamp, reverse=True)[:max_items]
    added = len({item["id"] for item in ordered} - existing_ids)
    return ordered, added


def render_json_feed(
    items: list[dict[str, Any]],
    *,
    home_url: str = DEFAULT_HOME_URL,
    feed_base_url: str = DEFAULT_FEED_BASE_URL,
) -> str:
    payload = {
        "version": JSON_FEED_VERSION,
        "title": "AI Intelligence Radar",
        "home_page_url": home_url,
        "feed_url": f"{feed_base_url.rstrip('/')}/feed.json",
        "description": "Source-linked signals from frontier AI companies and products.",
        "language": "zh-CN",
        "items": items,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_rss_feed(
    items: list[dict[str, Any]],
    *,
    home_url: str = DEFAULT_HOME_URL,
    feed_base_url: str = DEFAULT_FEED_BASE_URL,
) -> str:
    ET.register_namespace("atom", ATOM_NAMESPACE)
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "AI Intelligence Radar"
    ET.SubElement(channel, "link").text = home_url
    ET.SubElement(channel, "description").text = (
        "Source-linked signals from frontier AI companies and products."
    )
    ET.SubElement(channel, "language").text = "zh-cn"
    ET.SubElement(
        channel,
        f"{{{ATOM_NAMESPACE}}}link",
        {
            "href": f"{feed_base_url.rstrip('/')}/feed.xml",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )
    if items:
        latest = datetime.fromtimestamp(_item_timestamp(items[0]), tz=timezone.utc)
        ET.SubElement(channel, "lastBuildDate").text = format_datetime(latest)

    for feed_item in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = str(feed_item["title"])
        ET.SubElement(item, "link").text = str(feed_item["url"])
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = str(feed_item["id"])
        published = parse_published_at(str(feed_item["date_published"])).astimezone(timezone.utc)
        ET.SubElement(item, "pubDate").text = format_datetime(published)
        ET.SubElement(item, "description").text = str(feed_item["content_text"])
        for tag in feed_item.get("tags", []):
            ET.SubElement(item, "category").text = str(tag)

    ET.indent(rss, space="  ")
    return ET.tostring(rss, encoding="unicode", xml_declaration=True) + "\n"


def write_subscription_feeds(
    signals: Iterable[dict[str, Any]],
    output_dir: Path,
    *,
    max_items: int = 200,
    home_url: str = DEFAULT_HOME_URL,
    feed_base_url: str = DEFAULT_FEED_BASE_URL,
) -> dict[str, Any]:
    json_path = output_dir / "feed.json"
    rss_path = output_dir / "feed.xml"
    existing = _load_existing_items(json_path)
    items, added = merge_feed_items(existing, signals, max_items=max_items)
    json_content = render_json_feed(items, home_url=home_url, feed_base_url=feed_base_url)
    rss_content = render_rss_feed(items, home_url=home_url, feed_base_url=feed_base_url)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_temporary = json_path.with_suffix(".json.tmp")
    rss_temporary = rss_path.with_suffix(".xml.tmp")
    json_temporary.write_text(json_content, encoding="utf-8")
    rss_temporary.write_text(rss_content, encoding="utf-8")
    json_temporary.replace(json_path)
    rss_temporary.replace(rss_path)
    return {"json": json_path, "rss": rss_path, "items": len(items), "added": added}


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Radar signals as RSS and JSON feeds.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-items", type=int, default=200)
    parser.add_argument("--home-url", default=DEFAULT_HOME_URL)
    parser.add_argument("--feed-base-url", default=DEFAULT_FEED_BASE_URL)
    args = parser.parse_args()
    result = write_subscription_feeds(
        load_signals(args.input),
        args.output,
        max_items=args.max_items,
        home_url=args.home_url,
        feed_base_url=args.feed_base_url,
    )
    print(
        f"items={result['items']} added={result['added']} "
        f"rss={result['rss']} json={result['json']}"
    )


if __name__ == "__main__":
    main()
