from datetime import datetime, timezone
import unittest

from reporters.hourly_intelligence import build_intelligence
from reporters.morning_edition import item, research_candidates
from reporters.research_trends import summarize


NOW = datetime(2026, 11, 26, 2, tzinfo=timezone.utc)


class HourlyIntelligenceTests(unittest.TestCase):
    def test_morning_links_and_independent_publishers(self):
        title = "Meta Muse enables AI shopping workflow at Walmart"
        edition = item(title, "https://example.com/a", "Publisher A", NOW, "agent", "news")
        duplicate = item(title, "https://example.com/a-copy", "Publisher A", NOW, "agent", "news")
        second = item(title, "https://example.net/b", "Publisher B", NOW, "agent", "news")
        local = item("Spanish hospital pilots AI assistant in Madrid", "https://example.org/c", "A", NOW, "health", "news")
        morning = {"date": "2026-11-26", "items": [edition]}
        labels = {"agent": "个人 Agent"}
        single = build_intelligence([edition, duplicate, local], morning, labels, NOW)
        self.assertEqual(len(single["live"]), 1)
        self.assertEqual(single["live"][0]["morning"]["id"], edition["id"])
        self.assertEqual(single["signals"], [])
        result = build_intelligence([edition, second], morning, labels, NOW)
        self.assertEqual(result["signals"][0]["reports"], 2)
        self.assertEqual(result["signals"][0]["event_id"], result["live"][0]["id"])

    def test_research_counts_separate_venue_types_and_deduplicate(self):
        def record(identifier, title, source, pub_type="Journal Article"):
            return {"id": identifier, "title": title, "source": source, "firstPublicationDate": "2026-11-25",
                    "abstractText": "A study in a clinical setting.", "pubTypeList": {"pubType": [pub_type]}}
        rows = [
            record("1", "AI for clinical imaging", "MED"),
            record("2", "AI for clinical imaging", "PPR"),
            record("3", "Evaluating clinical decision support", "PPR"),
            record("4", "An editorial about AI", "MED", "Editorial"),
        ]
        output = summarize(rows, "2026-11-13", "2026-11-26")
        self.assertEqual(output["totals"], {"journal": 1, "preprint": 1})
        self.assertEqual(len(research_candidates(output, NOW)), 2)
