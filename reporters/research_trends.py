"""Summarize recent medical AI research by theme and publication type."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlencode

from reporters.morning_edition import PAPERS, fetch, local_date, write_json
from tools.public_feeds import _plain_text


JOURNALS = ("Nature Medicine", "NPJ Digital Medicine", "The Lancet Digital Health",
            "JAMA", "JAMA Network Open", "NEJM AI", "BMJ", "Radiology Artificial Intelligence")
PREPRINTS = {"medrxiv", "arxiv"}
AI_TOPIC = re.compile(r"\b(ai|artificial intelligence|large language model\w*|llms?|deep learning|machine learning|foundation model\w*)\b", re.I)
HEALTH_TOPIC = re.compile(r"\b(clinical|patient\w*|healthcare|medicine|hospital\w*|diagnos\w*|treatment\w*)\b", re.I)
THEMES = (
    ("影像与辅助诊断", r"\b(radiolog\w*|imaging|ultrasound|mammograph\w*|patholog\w*|diagnos\w*|MRI)\b"),
    ("临床工作流与决策支持", r"\b(workflow\w*|documentation|ambient|scribe\w*|decision support|clinical notes|triage)\b"),
    ("模型评测、安全与可靠性", r"\b(benchmark\w*|hallucinat\w*|bias|fairness|reliability|external validation|safety|robust\w*)\b"),
    ("疾病风险与患者管理", r"\b(risk predict\w*|prognos\w*|mortality|readmission|remote monitor\w*|patient management)\b"),
    ("药物研发与精准治疗", r"\b(drug discover\w*|drug develop\w*|therapeutic\w*|precision medicine|clinical trial\w*|omics|biomarker\w*)\b"),
    ("公共健康与医疗服务", r"\b(public health|population health|health services|health equity|health literacy|patient communication)\b"),
)


def summarize(records, start, end):
    themes = {}
    seen = set()
    totals = {"journal": 0, "preprint": 0}
    for record in sorted(records, key=lambda row: row.get("source") == "MED", reverse=True):
        source = record.get("source")
        kind = "journal" if source == "MED" else "preprint" if source == "PPR" else None
        if kind is None or not record.get("id") or not (start <= (record.get("firstPublicationDate") or "") <= end):
            continue
        types = {name.lower() for name in (record.get("pubTypeList") or {}).get("pubType", [])}
        if kind == "journal" and (types & {"preprint", "editorial", "letter", "comment", "news",
                                           "retracted publication", "published erratum", "retraction of publication"}):
            continue
        title = _plain_text(record.get("title") or "", 300)
        abstract = _plain_text(record.get("abstractText") or "", 10000)
        if not title or not abstract:
            continue
        title_key = re.sub(r"\W+", "", title).casefold()
        doi = (record.get("doi") or "").casefold()
        if title_key in seen or (doi and doi in seen):
            continue
        seen.add(title_key)
        if doi:
            seen.add(doi)
        totals[kind] += 1
        label = next((label for label, pattern in THEMES if re.search(pattern, title, re.I)), None)
        label = label or next((label for label, pattern in THEMES if re.search(pattern, abstract, re.I)), "其他医疗 AI 应用")
        theme = themes.setdefault(label, {"label": label, "journal": 0, "preprint": 0, "examples": []})
        theme[kind] += 1
        if sum(example["kind"] == kind for example in theme["examples"]) < 2:
            url = (f"https://pubmed.ncbi.nlm.nih.gov/{record['id']}/" if kind == "journal"
                   else f"https://europepmc.org/article/PPR/{record['id']}")
            theme["examples"].append({"title": title, "kind": kind, "url": url})
    return {
        "start": start, "end": end, "totals": totals,
        "themes": sorted(themes.values(), key=lambda row: (row["label"] != "其他医疗 AI 应用", row["journal"] + row["preprint"]), reverse=True),
    }


def collect_trends(now):
    start, end = local_date(now - timedelta(days=13)), local_date(now)
    records = []
    successful = []
    coverage = {}
    def search(source, term):
        scope = f'JOURNAL:"{term}"' if source == "MED" else f'TITLE_ABS:"{term}"'
        query = f'SRC:{source} AND {scope} AND FIRST_PDATE:[{start} TO {end}]'
        url = PAPERS + "?" + urlencode({"query": query, "pageSize": 30, "format": "json", "resultType": "core"})
        try:
            result = json.loads(fetch(url, timeout=22))
            return result["hitCount"], result["resultList"]["result"]
        except (OSError, ValueError, KeyError) as exc:
            print(f"research_source_failed source={source} term={term} error={type(exc).__name__}")
            return None

    jobs = [("MED", name) for name in JOURNALS] + [("PPR", "large language model"), ("PPR", "artificial intelligence")]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda job: search(*job), jobs))
    for (source, _), result in zip(jobs, results):
        label = "journal" if source == "MED" else "preprint"
        info = coverage.setdefault(label, {"matched": 0, "retrieved": 0, "sources_ok": 0, "sources_total": 0})
        info["sources_total"] += 1
        if result is None:
            continue
        matched, batch = result
        info["matched"] += matched
        info["retrieved"] += len(batch)
        info["sources_ok"] += 1
        if label not in successful:
            successful.append(label)
        for row in batch:
            text = f"{row.get('title', '')} {row.get('abstractText', '')}"
            if not AI_TOPIC.search(text):
                continue
            if source == "PPR" and (
                (row.get("bookOrReportDetails") or {}).get("publisher", "").casefold() not in PREPRINTS
                or not HEALTH_TOPIC.search(text)
            ):
                continue
            records.append(row)
    return {**summarize(records, start, end), "available": successful, "coverage": coverage}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/research-trends.json"))
    args = parser.parse_args()
    result = collect_trends(datetime.now(timezone.utc))
    if result["available"] and (result["themes"] or not args.output.exists()):
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, result)
    print(f"research_sources={len(result['available'])} themes={len(result['themes'])} counts={result['totals']}")


if __name__ == "__main__":
    main()
