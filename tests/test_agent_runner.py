import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from agent.runner import run_radar_agent


def make_source(source_id="example_releases"):
    return {
        "id": source_id,
        "name": f"{source_id} releases",
        "company": "Example AI",
        "source_tier": 1,
        "channel": "official_repository",
        "collection_mode": "atom",
        "url": f"https://example.com/{source_id}.atom",
        "status": "ready",
        "topics": ["coding-agents"],
    }


def make_signal(url, published_at):
    return {
        "title": f"Release {url.rsplit('/', 1)[-1]}",
        "canonical_url": url,
        "source_name": "Official releases",
        "source_tier": 1,
        "platform": "github",
        "company": "Example AI",
        "published_at": published_at,
        "summary": "A release summary.",
        "why_it_matters": "A product implication.",
        "evidence": ["Official release evidence."],
        "topics": ["coding-agents"],
        "impact_score": 3,
        "confidence": 0.98,
    }


class AgentRunnerTests(unittest.TestCase):
    def test_loop_collects_filters_writes_and_traces(self):
        sources = [make_source("one"), make_source("two")]

        def collector(source):
            if source["id"] == "one":
                return [make_signal("https://example.com/fresh", "2026-07-27T08:00:00+08:00")]
            return [make_signal("https://example.com/stale", "2026-07-20T08:00:00+08:00")]

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            trace = output / "trace.jsonl"
            state = run_radar_agent(
                sources,
                output,
                as_of=datetime.fromisoformat("2026-07-27T12:00:00+08:00"),
                collector=collector,
                trace_path=trace,
            )
            records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(state.status, "completed")
            self.assertEqual(state.stop_reason, "pipeline_complete")
            self.assertEqual(len(state.raw_signals), 2)
            self.assertEqual(len(state.filtered_signals), 1)
            self.assertEqual(state.result["written"], 1)
            self.assertTrue(Path(state.result["trend"]).exists())
            self.assertTrue(Path(state.result["briefing"]).exists())
            self.assertEqual(records[0]["event"], "run_started")
            self.assertEqual(records[-1]["event"], "run_finished")
            self.assertIn("planner_decision", {record["event"] for record in records})
            self.assertIn("tool_succeeded", {record["event"] for record in records})
            actions = {
                record["data"].get("action")
                for record in records
                if record["event"] == "planner_decision"
            }
            self.assertIn("write_briefing", actions)

    def test_loop_records_source_failure_and_continues(self):
        sources = [make_source("broken"), make_source("working")]

        def collector(source):
            if source["id"] == "broken":
                raise RuntimeError("temporary source failure")
            return [make_signal("https://example.com/fresh", "2026-07-27T08:00:00+08:00")]

        with tempfile.TemporaryDirectory() as directory:
            state = run_radar_agent(
                sources,
                Path(directory),
                as_of=datetime.fromisoformat("2026-07-27T12:00:00+08:00"),
                collector=collector,
            )
        self.assertEqual(state.status, "completed")
        self.assertEqual(state.result["written"], 1)
        self.assertEqual(len(state.errors), 1)

    def test_loop_fails_when_every_source_fails(self):
        sources = [make_source("broken-one"), make_source("broken-two")]

        def collector(_source):
            raise RuntimeError("source unavailable")

        with tempfile.TemporaryDirectory() as directory:
            state = run_radar_agent(
                sources,
                Path(directory),
                as_of=datetime.fromisoformat("2026-07-27T12:00:00+08:00"),
                collector=collector,
            )
        self.assertEqual(state.status, "failed")
        self.assertEqual(state.stop_reason, "all_sources_failed")
        self.assertEqual(state.result, {})


if __name__ == "__main__":
    unittest.main()
