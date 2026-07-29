import unittest

from tools.firecrawl_web import collect_firecrawl_web, parse_firecrawl_response


def make_source():
    return {
        "id": "example_news",
        "name": "Example Newsroom",
        "company": "Example AI",
        "source_tier": 1,
        "channel": "official_newsroom",
        "collection_mode": "firecrawl",
        "url": "https://example.com/news",
        "status": "requires_auth",
        "auth_env": ["FIRECRAWL_API_KEY"],
        "max_results": 2,
        "topics": ["agents", "research"],
    }


PAYLOAD = {
    "success": True,
    "data": {
        "json": {
            "articles": [
                {
                    "title": "New agent model",
                    "url": "/news/new-agent",
                    "published_at": "2026-07-27",
                    "summary": "The official team introduced a new agent model.",
                    "category": "Product",
                },
                {
                    "title": "Research update",
                    "url": "https://example.com/news/research",
                    "published_at": "2026-07-26T10:00:00Z",
                    "summary": "The lab published a new research result.",
                    "category": "Research",
                },
            ]
        }
    },
}


class FirecrawlWebTests(unittest.TestCase):
    def test_parses_structured_articles_into_signal_contract(self):
        signals = parse_firecrawl_response(PAYLOAD, make_source())

        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0]["company"], "Example AI")
        self.assertEqual(signals[0]["platform"], "official")
        self.assertEqual(
            signals[0]["canonical_url"],
            "https://example.com/news/new-agent",
        )
        self.assertEqual(signals[0]["impact_score"], 3)

    def test_collector_accepts_injected_fetcher(self):
        signals = collect_firecrawl_web(make_source(), fetcher=lambda _: PAYLOAD)

        self.assertEqual(signals[1]["title"], "Example AI · Research update")

    def test_rejects_failed_or_malformed_response(self):
        with self.assertRaisesRegex(ValueError, "Firecrawl scrape failed"):
            parse_firecrawl_response({"success": False, "error": "blocked"}, make_source())

        with self.assertRaisesRegex(ValueError, "articles"):
            parse_firecrawl_response({"success": True, "data": {}}, make_source())

    def test_rejects_non_firecrawl_source(self):
        source = make_source() | {"collection_mode": "rss"}
        with self.assertRaises(ValueError):
            collect_firecrawl_web(source, fetcher=lambda _: PAYLOAD)


if __name__ == "__main__":
    unittest.main()
