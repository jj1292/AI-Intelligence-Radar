"""Run product-focused evaluation cases against the current Radar pipeline."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from build_knowledge_base import build_knowledge_base, deduplicate_signals


DIMENSIONS = (
    "relevance",
    "evidence",
    "coverage",
    "dedup_newness",
    "judgment_value",
    "process_reliability",
)

DIMENSION_LABELS = {
    "relevance": "相关性",
    "evidence": "来源完整性",
    "coverage": "覆盖度",
    "dedup_newness": "去重与时效",
    "judgment_value": "判断价值",
    "process_reliability": "过程可靠性",
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    """Load one JSON object per non-empty line."""
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        if not isinstance(case, dict) or not case.get("id"):
            raise ValueError(f"Eval case on line {line_number} needs an id.")
        if not isinstance(case.get("signals"), list):
            raise ValueError(f"Eval case {case['id']} needs a signals array.")
        cases.append(case)
    if not cases:
        raise ValueError("Evaluation set is empty.")
    return cases


def _ratio_score(outcomes: Iterable[bool]) -> int:
    values = list(outcomes)
    if not values:
        return 2
    ratio = sum(values) / len(values)
    if ratio == 1:
        return 2
    if ratio >= 0.5:
        return 1
    return 0


def _detected_trends(report: str) -> set[str]:
    return set(re.findall(r"^- \*\*(.+?)\*\*：出现", report, flags=re.MULTILINE))


def _published_at_from_card(card: str) -> datetime | None:
    match = re.search(r'^published_at: "([^"]+)"$', card, flags=re.MULTILINE)
    return datetime.fromisoformat(match.group(1)) if match else None


def _with_frozen_insight(signal: dict[str, Any]) -> dict[str, Any]:
    """Keep evaluation deterministic while exercising the post-analysis contract."""
    if isinstance(signal.get("insight"), dict):
        return signal
    evidence = list(signal.get("evidence") or [])
    points = evidence[:2]
    while len(points) < 2:
        points.append(f"主题：{', '.join(signal.get('topics') or ['待分类'])}")
    return {
        **signal,
        "insight": {
            "core_idea": signal["summary"],
            "key_points": points,
            "analysis": signal["why_it_matters"],
            "takeaway": f"后续判断应围绕：{signal['why_it_matters']}",
        },
    }


def evaluate_case(case: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Execute one case and return product-level scores plus concrete gaps."""
    expectations = case.get("expectations", {})
    evaluation_time = datetime.fromisoformat(case["evaluation_time"])
    output_dir = workspace / case["id"]
    evaluated_signals = [_with_frozen_insight(signal) for signal in case["signals"]]
    result = build_knowledge_base(
        evaluated_signals,
        output_dir,
        evaluation_time.date(),
        as_of=evaluation_time,
        max_age_hours=expectations.get("max_age_hours", 48),
    )
    card_texts = [path.read_text(encoding="utf-8") for path in result["cards"]]
    trend_text = result["trend"].read_text(encoding="utf-8")
    actual_trends = _detected_trends(trend_text)
    expected_trends = set(expectations.get("trend_topics", []))
    forbidden_trends = set(expectations.get("forbidden_trend_topics", []))
    gaps: list[str] = []

    trend_checks = [topic in actual_trends for topic in expected_trends]
    trend_checks.extend(topic not in actual_trends for topic in forbidden_trends)
    relevance = _ratio_score(trend_checks)
    if relevance < 2:
        gaps.append(
            f"趋势判断不符合预期：expected={sorted(expected_trends)}, actual={sorted(actual_trends)}"
        )

    evidence_checks = [
        all(
            marker in card
            for marker in ("published_at:", "source:", "[查看原始来源](")
        )
        for card in card_texts
    ]
    evidence = _ratio_score(evidence_checks)
    if evidence < 2:
        gaps.append("部分知识卡缺少发布时间、证据段或原始来源链接。")

    expected_written = expectations.get("written_count", result["written"])
    difference = abs(result["written"] - expected_written)
    coverage = 2 if difference == 0 else 1 if difference == 1 else 0
    if coverage < 2:
        gaps.append(f"输出数量不符合任务意图：expected={expected_written}, actual={result['written']}")

    deduplicated_count = len(deduplicate_signals(case["signals"]))
    dedup_ok = deduplicated_count == expectations.get("deduplicated_count", deduplicated_count)
    freshness_ok = True
    max_age_hours = expectations.get("max_age_hours")
    if max_age_hours is not None:
        cutoff = evaluation_time - timedelta(hours=max_age_hours)
        dates = [_published_at_from_card(card) for card in card_texts]
        freshness_ok = all(published is not None and cutoff <= published <= evaluation_time for published in dates)
        if not freshness_ok:
            gaps.append(f"仍输出超过 {max_age_hours} 小时时效窗口的旧信号。")
    dedup_newness = _ratio_score([dedup_ok, freshness_ok])
    if not dedup_ok:
        gaps.append("去重后的信号数量不符合预期。")

    judgment_checks = [
        all(
            marker in card
            for marker in ("## 核心提炼", "## 关键要点", "## 分析", "## 输出")
        )
        for card in card_texts
    ]
    judgment_value = _ratio_score(judgment_checks)
    if judgment_value < 2:
        gaps.append("部分知识卡没有完成提炼、关键要点、分析与输出。")

    process_checks = [
        result["trend"].exists(),
        f"signal_count: {result['written']}" in trend_text,
        len(result["cards"]) == result["written"],
    ]
    process_reliability = _ratio_score(process_checks)
    if process_reliability < 2:
        gaps.append("生成文件、计数或趋势报告之间存在状态不一致。")

    vetoes: list[str] = []
    for signal, card in zip(deduplicate_signals(evaluated_signals), card_texts):
        if signal["source_tier"] == 3 and "source_tier: 3" not in card:
            vetoes.append("T3 社区信号未明确标注为社区层级。")
        if signal["canonical_url"] not in card:
            vetoes.append("知识卡未保留原始来源 URL。")

    scores = {
        "relevance": relevance,
        "evidence": evidence,
        "coverage": coverage,
        "dedup_newness": dedup_newness,
        "judgment_value": judgment_value,
        "process_reliability": process_reliability,
    }
    average = round(sum(scores.values()) / len(DIMENSIONS), 2)
    minimum_score = float(case.get("minimum_score", 1.8))
    return {
        "id": case["id"],
        "name": case.get("name", case["id"]),
        "scores": scores,
        "average": average,
        "passed": average >= minimum_score and not vetoes,
        "minimum_score": minimum_score,
        "vetoes": vetoes,
        "gaps": gaps,
        "received": len(case["signals"]),
        "written": result["written"],
    }


def evaluate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        results = [evaluate_case(case, Path(directory)) for case in cases]
    return {
        "case_count": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": sum(not result["passed"] for result in results),
        "average": round(sum(result["average"] for result in results) / len(results), 2),
        "results": results,
    }


def render_report(summary: dict[str, Any]) -> str:
    headers = [DIMENSION_LABELS[name] for name in DIMENSIONS]
    lines = [
        "# AI Intelligence Radar 评测基线",
        "",
        "> 评分采用 0–2 分：0=失败，1=部分达标，2=达标。一票否决项优先于平均分。",
        "",
        f"- 案例数：{summary['case_count']}",
        f"- 通过：{summary['passed']}",
        f"- 未通过：{summary['failed']}",
        f"- 平均分：{summary['average']}/2",
        "",
        "## 评分矩阵",
        "",
        "| 案例 | " + " | ".join(headers) + " | 平均分 | 结果 |",
        "| --- | " + " | ".join([":---:"] * len(headers)) + " | :---: | :---: |",
    ]
    for result in summary["results"]:
        score_cells = [str(result["scores"][dimension]) for dimension in DIMENSIONS]
        lines.append(
            f"| {result['name']} | "
            + " | ".join(score_cells)
            + f" | {result['average']} | {'✅ 通过' if result['passed'] else '❌ 未通过'} |"
        )

    lines.extend(["", "## 发现的缺口", ""])
    has_gap = False
    for result in summary["results"]:
        findings = [*result["vetoes"], *result["gaps"]]
        if findings:
            has_gap = True
            lines.append(f"### {result['name']}")
            lines.append("")
            lines.extend(f"- {finding}" for finding in findings)
            lines.append("")
    if not has_gap:
        lines.append("- 当前案例未发现缺口；需要继续增加边界与风险案例。")
        lines.append("")

    lines.extend(
        [
            "## 如何使用这份基线",
            "",
            "1. 修复一个明确缺口，不同时改多个变量。",
            "2. 使用同一组案例重新运行评测。",
            "3. 只有评分提高且没有新增一票否决项，才把变化视为产品改进。",
            "4. 自动评分只覆盖可机械检查的部分；相关性、判断质量仍需定期人工抽检。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the AI Intelligence Radar pipeline.")
    parser.add_argument("--cases", type=Path, default=Path("evals/cases.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("evals/baseline-report.md"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any case misses its threshold.")
    args = parser.parse_args()

    summary = evaluate_cases(load_cases(args.cases))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(summary), encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"cases={summary['case_count']} passed={summary['passed']} "
        f"failed={summary['failed']} average={summary['average']}/2"
    )
    print(f"report={args.output}")
    if args.strict and summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
