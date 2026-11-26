import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

from reporters.morning_edition import choose, item, parse_news, parse_papers, publish, similar


NOW = datetime(2026, 11, 26, 3, tzinfo=timezone.utc)
CONFIG = json.loads(Path("config/morning-edition.json").read_text(encoding="utf-8"))


class MorningEditionTests(unittest.TestCase):
    def test_same_event_across_different_publishers(self):
        a = item("Amazon and Meta reportedly in talks to lift blockade on AI agent Muse",
                 "https://publisher-a.example/report", "A", NOW, "agent", "news")
        b = item("Amazon is reportedly in talks to end Muse AI shopping block",
                 "https://publisher-b.example/report", "B", NOW, "industry", "news")
        self.assertTrue(similar(a, b))

    def test_selection_balances_topics_and_skips_old_and_duplicate_news(self):
        titles = {
            "agent": ["Muse connects to Walmart", "Personal assistant learns to manage calendars"],
            "industry": ["Startup raises funding for inference", "New model changes enterprise pricing"],
            "health": ["Regulator publishes clinical software guidance", "Stroke triage goes live in Alaska",
                       "Hospital deploys ambient documentation"],
            "product": ["How to design task completion evaluations"],
            "research": ["Vision models predict radiology findings", "Trial measures patient follow-up rates"],
        }
        rows = [
            item(title, f"https://example.org/{category}/{index}",
                 f"{category} source {index}", NOW, category,
                 "official" if category == "health" and not index else "news")
            for category, stories in titles.items()
            for index, title in enumerate(stories)
        ]
        stale = item("Stale article", "https://example.org/stale", "Outlet", NOW - timedelta(days=8), "agent", "news")
        duplicate = {**rows[0], "category": "industry"}
        selected = choose([stale, duplicate, *rows], CONFIG, NOW)
        self.assertEqual(len(selected), 10)
        self.assertEqual(len({row["url"] for row in selected}), 10)
        self.assertNotIn(stale, selected)
        for category, section in CONFIG.items():
            self.assertEqual(sum(row["category"] == category for row in selected), section["slots"])
        self.assertNotIn(rows[0]["url"], [row["url"] for row in choose(rows, CONFIG, NOW, [rows[0]])])

    def test_policy_and_preprint_types_are_retained(self):
        news = b"""<rss><channel><item><title>AI regulation for medical devices - FDA</title>
          <link>https://news.google.com/rss/articles/example</link><source url="https://fda.gov">FDA</source>
          <pubDate>Wed, 25 Nov 2026 13:00:00 GMT</pubDate></item></channel></rss>"""
        self.assertEqual(list(parse_news(news, "health"))[0]["kind"], "official")
        self.assertEqual(list(parse_news(news, "agent")), [])
        data = json.dumps({"resultList": {"result": [
            {"title": "A study", "abstractText": "A &amp; B", "source": "PPR",
             "id": "PPR123", "firstPublicationDate": "2026-11-25"},
        ]}})
        paper = list(parse_papers(data))[0]
        self.assertEqual(paper["kind"], "preprint")
        self.assertEqual(paper["summary"], "A & B")

    def test_archive_and_rss_keep_latest_visible_when_backfilling(self):
        row = item("An article", "https://example.org/news", "Outlet", NOW, "agent", "news")
        with TemporaryDirectory() as directory:
            output = Path(directory)
            publish([row], CONFIG, output, NOW, "2026-11-26")
            publish([row], CONFIG, output, NOW, "2026-11-25")
            latest = json.loads((output / "morning-edition.json").read_text(encoding="utf-8"))
            self.assertEqual(latest["date"], "2026-11-26")
            rss = ET.parse(output / "morning-edition.xml")
            self.assertIn("edition=2026-11-26", rss.findtext("channel/item/link"))
            self.assertEqual(len(rss.findall("channel/item")), 2)
