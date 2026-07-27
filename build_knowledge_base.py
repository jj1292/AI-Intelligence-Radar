"""Convert normalized AI signals into Obsidian-friendly knowledge cards."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REQUIRED_FIELDS = {
    "title",
    "canonical_url",
    "source_name",
    "source_tier",
    "platform",
    "company",
    "published_at",
    "summary",
    "why_it_matters",
    "topics",
}


def load_signals(path: Path) -> list[dict[str, Any]]:
    signals = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(signals, list):
        raise ValueError("Signals input must be a JSON array.")
    for index, signal in enumerate(signals, start=1):
        if not isinstance(signal, dict):
            raise ValueError(f"Signal {index} must be an object.")
        missing = sorted(REQUIRED_FIELDS - set(signal))
        if missing:
            raise ValueError(f"Signal {index} missing fields: {missing}")
        if signal["source_tier"] not in {1, 2, 3}:
            raise ValueError(f"Signal {index} has an invalid source_tier.")
        if not isinstance(signal["topics"], list) or not signal["topics"]:
            raise ValueError(f"Signal {index} must have at least one topic.")
    return signals


def deduplicate_signals(signals: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[dict[str, Any]] = []
    for signal in signals:
        url = signal["canonical_url"].strip()
        title_key = re.sub(r"\W+", "", signal["title"], flags=re.UNICODE).lower()
        if url in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title_key)
        unique.append(signal)
    return unique


def parse_published_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    published_at = datetime.fromisoformat(normalized)
    if published_at.tzinfo is None:
        raise ValueError("published_at must include a timezone offset.")
    return published_at


def filter_signals_by_freshness(
    signals: Iterable[dict[str, Any]],
    as_of: datetime,
    max_age_hours: float = 48,
) -> list[dict[str, Any]]:
    if as_of.tzinfo is None:
        raise ValueError("as_of must include a timezone offset.")
    if max_age_hours <= 0:
        raise ValueError("max_age_hours must be greater than zero.")

    cutoff = as_of.astimezone(timezone.utc) - timedelta(hours=max_age_hours)
    upper_bound = as_of.astimezone(timezone.utc)
    fresh: list[dict[str, Any]] = []
    for signal in signals:
        published_at = parse_published_at(signal["published_at"]).astimezone(timezone.utc)
        if cutoff <= published_at <= upper_bound:
            fresh.append(signal)
    return fresh


def _default_as_of(signals: list[dict[str, Any]], report_date: date) -> datetime:
    tz = timezone.utc
    if signals:
        tz = parse_published_at(signals[0]["published_at"]).tzinfo or timezone.utc
    return datetime.combine(report_date, time.max, tzinfo=tz)


def _yaml_text(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _slug(signal: dict[str, Any]) -> str:
    company = re.sub(r"[^a-z0-9]+", "-", signal["company"].lower()).strip("-") or "signal"
    digest = hashlib.sha256(signal["canonical_url"].encode("utf-8")).hexdigest()[:10]
    return f"{company}-{digest}"


def render_knowledge_card(signal: dict[str, Any], card_date: date) -> str:
    topics = ", ".join(_yaml_text(topic) for topic in signal["topics"])
    evidence = signal.get("evidence") or []
    evidence_lines = [f"- {item}" for item in evidence[:3]] or ["- 暂无可安全摘录的短证据，请回到原文核验。"]
    impact = signal.get("impact_score", "待评估")
    confidence = signal.get("confidence", "待评估")

    lines = [
        "---",
        "type: ai-intelligence-signal",
        f"date: {card_date.isoformat()}",
        f"published_at: {_yaml_text(signal['published_at'])}",
        f"company: {_yaml_text(signal['company'])}",
        f"source: {_yaml_text(signal['source_name'])}",
        f"source_tier: {signal['source_tier']}",
        f"platform: {_yaml_text(signal['platform'])}",
        f"topics: [{topics}]",
        f"url: {_yaml_text(signal['canonical_url'])}",
        "---",
        "",
        f"# {signal['title']}",
        "",
        "## 一句话结论",
        "",
        signal["summary"],
        "",
        "## 为什么重要",
        "",
        signal["why_it_matters"],
        "",
        "## 一手证据",
        "",
        *evidence_lines,
        "",
        "## 判断与边界",
        "",
        f"- 影响评分：{impact}/5" if isinstance(impact, int) else f"- 影响评分：{impact}",
        f"- 可信度：{confidence}",
        f"- 来源等级：T{signal['source_tier']}（T1 官方、T2 一手账号、T3 社区信号）",
        "- 本卡片保存的是摘要和判断，不替代原文；重要结论需回到来源复核。",
        "",
        f"[查看原始来源]({signal['canonical_url']})",
        "",
    ]
    return "\n".join(lines)


def render_trend_report(signals: list[dict[str, Any]], report_date: date) -> str:
    company_counts = Counter(signal["company"] for signal in signals)
    topic_sources: dict[str, set[tuple[str, str]]] = {}
    for signal in signals:
        source_key = (signal["company"], signal["source_name"])
        for topic in signal["topics"]:
            topic_sources.setdefault(topic, set()).add(source_key)
    trend_topics = sorted(
        ((topic, len(sources)) for topic, sources in topic_sources.items() if len(sources) >= 2),
        key=lambda item: (-item[1], item[0]),
    )

    lines = [
        "---",
        "type: ai-trend-radar",
        f"date: {report_date.isoformat()}",
        f"signal_count: {len(signals)}",
        "---",
        "",
        f"# AI 趋势雷达 - {report_date.isoformat()}",
        "",
        "## 今日判断",
        "",
    ]
    if trend_topics:
        for topic, count in trend_topics:
            lines.append(f"- **{topic}**：出现 {count} 个独立来源，进入持续观察列表。")
    else:
        lines.append("- 暂无达到两条独立信号的趋势候选，避免把单条新闻误判成趋势。")

    lines.extend(["", "## 公司信号密度", ""])
    for company, count in company_counts.most_common():
        lines.append(f"- {company}：{count} 条")

    lines.extend(["", "## 信号清单", ""])
    for signal in signals:
        topics = ", ".join(signal["topics"])
        lines.append(f"- [{signal['title']}]({signal['canonical_url']}) · {signal['company']} · {topics}")

    lines.extend(
        [
            "",
            "## 下一步观察",
            "",
            "- 同一主题是否在不同公司、官方发布和社区反馈中连续出现。",
            "- 产品声明是否转化为可复现能力、真实用例或开发者采用。",
            "- 社区热度是否有 T1 官方证据支持，避免把情绪当成事实。",
            "",
        ]
    )
    return "\n".join(lines)


def build_knowledge_base(
    signals: list[dict[str, Any]],
    output_dir: Path,
    report_date: date,
    *,
    as_of: datetime | None = None,
    max_age_hours: float = 48,
) -> dict[str, Any]:
    effective_as_of = as_of or _default_as_of(signals, report_date)
    fresh = filter_signals_by_freshness(signals, effective_as_of, max_age_hours)
    unique = deduplicate_signals(fresh)
    cards_dir = output_dir / "signals" / report_date.isoformat()
    trends_dir = output_dir / "trends"
    cards_dir.mkdir(parents=True, exist_ok=True)
    trends_dir.mkdir(parents=True, exist_ok=True)

    card_paths = []
    for signal in unique:
        card_path = cards_dir / f"{_slug(signal)}.md"
        card_path.write_text(render_knowledge_card(signal, report_date), encoding="utf-8")
        card_paths.append(card_path)

    trend_path = trends_dir / f"{report_date.isoformat()}-trend-radar.md"
    trend_path.write_text(render_trend_report(unique, report_date), encoding="utf-8")
    return {
        "received": len(signals),
        "fresh": len(fresh),
        "freshness_excluded": len(signals) - len(fresh),
        "written": len(card_paths),
        "cards": card_paths,
        "trend": trend_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an Obsidian-friendly AI intelligence knowledge base.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--as-of", help="ISO 8601 timestamp with timezone; defaults to end of --date")
    parser.add_argument("--max-age-hours", type=float, default=48)
    args = parser.parse_args()
    result = build_knowledge_base(
        load_signals(args.input),
        args.output,
        date.fromisoformat(args.date),
        as_of=datetime.fromisoformat(args.as_of.replace("Z", "+00:00")) if args.as_of else None,
        max_age_hours=args.max_age_hours,
    )
    print(
        f"received={result['received']} fresh={result['fresh']} "
        f"excluded={result['freshness_excluded']} written={result['written']}"
    )
    print(f"trend={result['trend']}")


if __name__ == "__main__":
    main()
