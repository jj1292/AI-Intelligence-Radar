import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from reporters.subscription_feed import merge_feed_items, write_subscription_feeds


def make_signal(
    title="OpenAI model update",
    *,
    url="https://x.com/OpenAI/status/100",
    published_at="2026-07-27T08:00:00+00:00",
):
    return {
        "title": title,
        "canonical_url": url,
        "source_name": "Frontier AI official X accounts",
        "source_tier": 2,
        "platform": "x",
        "company": "OpenAI",
        "author": "@OpenAI",
        "published_at": published_at,
        "summary": "A concise source-backed summary.",
        "why_it_matters": "A concrete product implication.",
        "evidence": ["Source evidence."],
        "topics": ["models", "agents"],
        "impact_score": 3,
        "confidence": 0.85,
    }


class SubscriptionFeedTests(unittest.TestCase):
    def test_writes_valid_rss_and_json_feeds(self):
        with tempfile.TemporaryDirectory() as directory:
            result = write_subscription_feeds([make_signal()], Path(directory))
            payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
            root = ET.parse(result["rss"]).getroot()

        self.assertEqual(result["items"], 1)
        self.assertEqual(result["added"], 1)
        self.assertEqual(payload["items"][0]["id"], "https://x.com/OpenAI/status/100")
        self.assertEqual(payload["items"][0]["_radar"]["impact_score"], 3)
        self.assertEqual(payload["items"][0]["_radar"]["confidence"], 0.85)
        self.assertEqual(
            payload["items"][0]["_radar"]["evidence"],
            ["Source evidence."],
        )
        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.findtext("channel/item/title"), "OpenAI model update")

    def test_merges_history_deduplicates_and_keeps_newest_items(self):
        old_signal = make_signal(
            "Old",
            url="https://example.com/old",
            published_at="2026-07-25T08:00:00+00:00",
        )
        existing, _ = merge_feed_items([], [old_signal])
        new_signal = make_signal(
            "New",
            url="https://example.com/new",
            published_at="2026-07-27T08:00:00+00:00",
        )

        merged, added = merge_feed_items(existing, [old_signal, new_signal], max_items=2)

        self.assertEqual([item["title"] for item in merged], ["New", "Old"])
        self.assertEqual(added, 1)

    def test_rejects_corrupt_existing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "feed.json").write_text('{"items": "broken"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON feed history"):
                write_subscription_feeds([make_signal()], output)


if __name__ == "__main__":
    unittest.main()
