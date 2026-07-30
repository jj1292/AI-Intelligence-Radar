import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.insight_analysis import analyze_signals


def make_signal(url="https://www.anthropic.com/news/example"):
    return {
        "title": "Anthropic · A material product change",
        "canonical_url": url,
        "source_name": "Anthropic Newsroom",
        "source_tier": 1,
        "platform": "official",
        "company": "Anthropic",
        "published_at": "2026-07-29T08:00:00+00:00",
        "summary": "Anthropic changed how long-running agents preserve context.",
        "why_it_matters": "Legacy field retained for backward compatibility.",
        "evidence": ["A source-backed fact."],
        "topics": ["claude", "agents"],
        "impact_score": 4,
        "confidence": 0.98,
    }


def insight():
    return {
        "core_idea": "长期任务的竞争焦点从单次回答转向可持续维护上下文。",
        "key_points": [
            "系统压缩旧上下文，同时保留任务目标与关键状态。",
            "开发者需要重新设计检查点和失败恢复。",
        ],
        "analysis": "这改变了 Agent 的工程瓶颈：模型能力不再是唯一上限，状态治理开始决定任务能否稳定完成。",
        "takeaway": "评估 Agent 时，应增加长任务恢复率与状态一致性，而不只看单轮正确率。",
    }


class InsightAnalysisTests(unittest.TestCase):
    def test_analyzes_article_with_structured_contract(self):
        seen = {}

        def model_client(signal, article_text):
            seen["title"] = signal["title"]
            seen["article"] = article_text
            return insight()

        result = analyze_signals(
            [make_signal()],
            article_fetcher=lambda _url: (
                "Full article body with implementation details. " * 20
            ),
            model_client=model_client,
        )

        self.assertEqual(result.analyzed, 1)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.signals[0]["insight"], insight())
        self.assertIn("implementation details", seen["article"])

    def test_reuses_existing_analysis_without_model_call(self):
        with tempfile.TemporaryDirectory() as directory:
            feed = Path(directory) / "feed.json"
            feed.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": make_signal()["canonical_url"],
                                "_radar": {"insight": insight()},
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = analyze_signals(
                [make_signal()],
                existing_feed_path=feed,
                model_client=lambda *_args: self.fail("model should not be called"),
            )

        self.assertEqual(result.reused, 1)
        self.assertEqual(result.analyzed, 0)
        self.assertEqual(result.signals[0]["insight"], insight())

    def test_prioritizes_official_articles_and_skips_preview_releases(self):
        preview = make_signal("https://github.com/example/releases/alpha")
        preview.update(
            {
                "title": "Example · 2.0.0-alpha.1",
                "platform": "github",
                "published_at": "2026-07-30T09:00:00+00:00",
            }
        )
        stable = make_signal("https://github.com/example/releases/stable")
        stable.update(
            {
                "title": "Example · 1.9.0",
                "platform": "github",
                "published_at": "2026-07-30T08:00:00+00:00",
            }
        )
        called = []

        def model_client(signal, _article_text):
            called.append(signal["canonical_url"])
            return insight()

        result = analyze_signals(
            [preview, stable, make_signal()],
            max_new=1,
            article_fetcher=lambda _url: "Grounded article content. " * 30,
            model_client=model_client,
        )

        self.assertEqual(called, [make_signal()["canonical_url"]])
        self.assertNotIn("insight", result.signals[0])
        self.assertNotIn("insight", result.signals[1])
        self.assertIn("insight", result.signals[2])

    def test_does_not_fake_analysis_without_model_access(self):
        with patch.dict(
            "os.environ",
            {"GITHUB_TOKEN": "", "RADAR_ANALYSIS_TOKEN": ""},
            clear=False,
        ):
            result = analyze_signals([make_signal()], token="")

        self.assertNotIn("insight", result.signals[0])
        self.assertEqual(result.analyzed, 0)
        self.assertEqual(result.skipped, 1)


if __name__ == "__main__":
    unittest.main()
