import unittest
from pathlib import Path

from evaluate_radar import evaluate_cases, load_cases, render_report


CASES_PATH = Path(__file__).parents[1] / "evals" / "cases.jsonl"


class EvaluateRadarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(CASES_PATH)
        cls.summary = evaluate_cases(cls.cases)

    def test_loads_three_product_cases(self):
        self.assertEqual(len(self.cases), 3)
        self.assertEqual(
            {case["id"] for case in self.cases},
            {"normal_multi_source_trend", "edge_no_false_trend", "risk_stale_signal"},
        )

    def test_baseline_closes_freshness_gap(self):
        results = {result["id"]: result for result in self.summary["results"]}
        stale_case = results["risk_stale_signal"]
        self.assertTrue(stale_case["passed"])
        self.assertEqual(stale_case["scores"]["dedup_newness"], 2)
        self.assertEqual(stale_case["gaps"], [])

    def test_report_contains_scores_and_no_known_gap(self):
        report = render_report(self.summary)
        self.assertIn("评分矩阵", report)
        self.assertIn("去重与时效", report)
        self.assertIn("当前案例未发现缺口", report)


if __name__ == "__main__":
    unittest.main()
