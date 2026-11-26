"""Publish hourly news and link important events to the latest morning edition."""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

from reporters.morning_edition import collect, focus, in_scope, similar, write_json, x_candidates


AGENT_THEMES = (
    ("跨应用执行与授权", r"\b(computer use|cross-app|browser|checkout|email|shopping|workflow|blockade)\b|跨应用|浏览器|购物|工作流|打电话",
     "对照哪些步骤能完成、哪些步骤仍需用户授权，以及应用接口在其中的作用。"),
    ("模型能力与任务可靠性", r"\b(reasoning|benchmark|reliability|evaluation|memory|long-running|context|accuracy|inflection points)\b|推理|评测|记忆|可靠|长任务",
     "把推理、记忆和工具调用的变化对应到任务完成率、接管次数和失败恢复。"),
    ("从助手功能到实际采用", r"\b(partnership|pilot|adopt\w*|launch\w*|integration|distribution)\b|上线|落地|接入|合作|用户",
     "区分可用范围、用户试用和持续使用，跟踪试点能否走到常用任务。"),
)


def agent_themes(rows):
    output = []
    for title, pattern, question in AGENT_THEMES:
        evidence = []
        for row in rows:
            content = row["title"] + " " + row.get("summary", "") + " " + (row.get("insight") or {}).get("digest", "")
            agent_article = row["category"] == "agent" or (
                row["category"] == "product" and re.search(r"\bagents?\b|智能体", content, re.I)
            )
            if not agent_article or not re.search(pattern, content, re.I):
                continue
            if any(publisher(row) == publisher(other) or similar(row, other) for other in evidence):
                continue
            evidence.append(row)
            if len(evidence) == 3:
                break
        if evidence:
            output.append({
                "title": title, "question": question,
                "links": [{key: row[key] for key in ("title", "source", "url")} for row in evidence],
            })
    return output


def timestamp(row):
    return datetime.fromisoformat(row["published_at"])


def publisher(row):
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", row["source"].casefold().removesuffix(".com"))


def build_watchlists(config, candidates, now):
    def event_type(title):
        if re.search(r"\b(IPO|funding|raises|raised|acqui\w*|investment|earnings|financial results|revenue)\b|融资|上市|配售|财报|业绩|收购|招股", title, re.I):
            return "资本与业绩"
        if re.search(r"\b(model|weights|inference|benchmark)\b|大模型|开源|模型|权重", title, re.I):
            return "模型与研究"
        return "产品与公司动态"

    recent = sorted(
        (row for row in candidates if in_scope(row) and now - timedelta(days=7) <= timestamp(row) <= now),
        key=timestamp, reverse=True,
    )
    groups = []
    for key, group in config.items():
        subjects = []
        for subject in group["subjects"]:
            aliases = [
                (r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])") if alias.isascii()
                else re.escape(alias)
                for alias in subject["aliases"]
            ]
            matcher = re.compile("|".join(aliases), re.IGNORECASE)
            stories = []
            for row in recent:
                if not matcher.search(row["title"]) or any(similar(row, old) for old in stories):
                    continue
                stories.append(row)
                if len(stories) == 12:
                    break
            first = stories[:1]
            if first:
                other = next((row for row in stories[1:] if event_type(row["title"]) != event_type(first[0]["title"])), None)
                first.extend([other] if other else stories[1:2])
            card = {"name": subject["name"], "url": subject["url"], "stories": [
                {**{field: row[field] for field in ("title", "url", "source", "published_at")},
                 "type": event_type(row["title"])} for row in first
            ]}
            reference = subject.get("reference")
            if reference and (now.date() - timedelta(days=30)).isoformat() <= reference["date"] <= now.date().isoformat():
                card["reference"] = reference
            subjects.append(card)
        groups.append({"id": key, "label": group["label"], "subjects": subjects})
    return groups


def build_intelligence(candidates, morning, categories, now):
    fresh = [
        row for row in candidates
        if in_scope(row) and now - timedelta(days=3) <= timestamp(row) <= now
    ]
    morning_items = [
        row for row in morning.get("items", [])
        if in_scope(row) and now - timedelta(days=7) <= timestamp(row) <= now
    ]
    ranked = sorted(
        fresh,
        key=lambda row: (bool(focus(row)), row["kind"] != "x", timestamp(row)),
        reverse=True,
    )
    groups = []
    for row in ranked:
        event = next((group for group in groups if similar(row, group[0])), None)
        if event is None:
            groups.append([row])
        elif all(other["url"] != row["url"] and publisher(other) != publisher(row) for other in event):
            event.append(row)

    live = []
    signals = []
    source_counts = Counter()
    category_counts = Counter()
    matched = set()

    def wrap(row, sources, edition=None, event_id=None):
        return {
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "region": focus(row),
            "published_at": row["published_at"],
            "sources": [
                {key: source[key] for key in ("source", "url", "kind")} for source in sources[:3]
            ],
            "morning": {"date": morning["date"], "id": edition["id"]} if edition else None,
            "event_id": event_id,
        }

    for group in groups:
        lead = group[0]
        if len(live) >= 18:
            break
        if source_counts[publisher(lead)] >= 3 or category_counts[lead["category"]] >= 6:
            continue
        edition = next((item for item in morning_items if any(similar(item, row) for row in group)), None)
        link = wrap(lead, group, edition, lead["id"])
        live.append(link)
        source_counts[publisher(lead)] += 1
        category_counts[lead["category"]] += 1
        distinct_reports = {publisher(row) for row in group if row["kind"] in {"news", "official"}}
        if edition:
            matched.add(edition["id"])
            if edition["kind"] in {"news", "official"}:
                distinct_reports.add(publisher(edition))
        if (edition and edition.get("insight")) or len(distinct_reports) >= 2 or (
            edition and (lead["kind"] == "official" or edition["kind"] == "official")
        ):
            signal = {**link, "reports": len(distinct_reports), "insight": edition.get("insight") if edition else None}
            if edition and publisher(edition) not in {publisher(row) for row in group}:
                signal["sources"] = wrap(lead, [*group[:2], edition])["sources"]
            signals.append(signal)

    for row in morning_items:
        if row["id"] not in matched and row.get("insight"):
            signals.append({
                **wrap(row, [row], row),
                "reports": 1 if row["kind"] in {"news", "official"} else 0,
                "insight": row["insight"],
            })
    signals.sort(key=lambda row: (bool(row["morning"] and row["event_id"]), bool(row["insight"]),
                                  row["reports"], timestamp(row)), reverse=True)
    # Keep daily signals varied when multiple reports cover the same topic.
    category_counts = Counter()
    selected = []
    for row in signals:
        if category_counts[row["category"]] < 2:
            selected.append(row)
            category_counts[row["category"]] += 1
        if len(selected) == 6:
            break
    return {"updated_at": now.isoformat(), "categories": categories, "live": live, "signals": selected,
            "agent_themes": agent_themes(ranked + morning_items)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/intelligence.json"))
    parser.add_argument("--data-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()
    config = json.loads(Path("config/morning-edition.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    morning_path = args.data_dir / "morning-edition.json"
    morning = json.loads(morning_path.read_text(encoding="utf-8")) if morning_path.exists() else {}
    categories = {key: value["label"] for key, value in config.items()}
    rows = collect(config, now, include_papers=False) + x_candidates(args.data_dir / "feed.json")
    result = build_intelligence(rows, morning, categories, now)
    watchlists = json.loads(Path("config/watchlists.json").read_text(encoding="utf-8"))
    result["watchlists"] = build_watchlists(watchlists, rows, now)
    if not result["live"] and args.output.exists():
        print("No recent headlines. Retained previous hourly snapshot.")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(f"live={len(result['live'])} signals={len(result['signals'])}")


if __name__ == "__main__":
    main()
