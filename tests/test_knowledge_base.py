import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from build_knowledge_base import (
    build_knowledge_base,
    deduplicate_signals,
    filter_signals_by_freshness,
    load_signals,
)
from source_registry import load_source_registry, summarize_sources


def make_signal(url="https://example.com/one", title="Agent update", company="OpenAI"):
    return {
        "title": title,
        "canonical_url": url,
        "source_name": "Official changelog",
        "source_tier": 1,
        "platform": "official",
        "company": company,
        "published_at": "2026-07-22T08:00:00+08:00",
        "summary": "A concise summary.",
        "why_it_matters": "A concrete product implication.",
        "evidence": ["A short source-backed fact."],
        "topics": ["coding-agents"],
        "impact_score": 4,
        "confidence": 0.9,
    }


class KnowledgeBaseTests(unittest.TestCase):
    def test_deduplicates_by_canonical_url(self):
        signals = [make_signal(), make_signal(title="Duplicate title variant")]
        self.assertEqual(len(deduplicate_signals(signals)), 1)

    def test_filters_signals_outside_48_hour_window(self):
        signals = [
            make_signal(),
            make_signal(
                "https://example.com/stale",
                "Stale agent update",
                "Example AI",
            )
            | {"published_at": "2026-07-18T08:00:00+08:00"},
        ]
        fresh = filter_signals_by_freshness(
            signals,
            datetime.fromisoformat("2026-07-22T12:00:00+08:00"),
            48,
        )
        self.assertEqual([signal["title"] for signal in fresh], ["Agent update"])

    def test_builds_cards_and_trend_report(self):
        signals = [
            make_signal(),
            make_signal("https://example.com/two", "Another agent update", "Anthropic"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = build_knowledge_base(signals, Path(directory), date(2026, 7, 22))
            self.assertEqual(result["written"], 2)
            self.assertTrue(result["trend"].exists())
            trend = result["trend"].read_text(encoding="utf-8")
            self.assertIn("coding-agents", trend)
            self.assertIn("2 个独立来源", trend)
            card = result["cards"][0].read_text(encoding="utf-8")
            self.assertIn("为什么重要", card)
            self.assertIn("查看原始来源", card)

    def test_build_reports_freshness_exclusions(self):
        signals = [
            make_signal(),
            make_signal("https://example.com/stale", "Stale update")
            | {"published_at": "2026-07-18T08:00:00+08:00"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = build_knowledge_base(
                signals,
                Path(directory),
                date(2026, 7, 22),
                as_of=datetime.fromisoformat("2026-07-22T12:00:00+08:00"),
            )
        self.assertEqual(result["written"], 1)
        self.assertEqual(result["freshness_excluded"], 1)

    def test_same_source_releases_do_not_create_false_trend(self):
        signals = [
            make_signal(),
            make_signal("https://example.com/two", "Another release"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = build_knowledge_base(signals, Path(directory), date(2026, 7, 22))
            trend = result["trend"].read_text(encoding="utf-8")
        self.assertIn("暂无达到两条独立信号", trend)
        self.assertNotIn("**coding-agents**", trend)

    def test_rejects_incomplete_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signals.json"
            path.write_text(json.dumps([{"title": "missing fields"}]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_signals(path)

    def test_source_registry_is_valid(self):
        path = Path(__file__).parents[1] / "config" / "sources.json"
        sources = load_source_registry(path)
        summary = summarize_sources(sources)
        self.assertIn("sources=10", summary)
        self.assertIn("ready=2", summary)
        self.assertIn("adapter_required=6", summary)
        self.assertIn("requires_auth=2", summary)


if __name__ == "__main__":
    unittest.main()
