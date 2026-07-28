import unittest

from tools.anthropic_news import collect_anthropic_news, parse_anthropic_news


HTML_FIXTURE = """
<html><body>
  <a href="/news/claude-opus-example" class="featured-content">
    <h2 class="featuredTitle">Introducing Claude Opus Example</h2>
    <span class="caption bold">Product</span>
    <time class="date">Jul 27, 2026</time>
    <p class="body">A major update for long-running agents.</p>
  </a>
  <ul>
    <li>
      <a href="/news/open-weights-example" class="listItem">
        <time class="date">Jul 26, 2026</time>
        <span class="subject">Announcements</span>
        <span class="title">Our position on open models</span>
      </a>
    </li>
    <li>
      <a href="/news/claude-opus-example" class="listItem">
        <time class="date">Jul 27, 2026</time>
        <span class="subject">Product</span>
        <span class="title">Introducing Claude Opus Example</span>
      </a>
    </li>
  </ul>
</body></html>
"""


def make_source(**overrides):
    source = {
        "id": "anthropic_newsroom",
        "name": "Anthropic Newsroom",
        "company": "Anthropic",
        "source_tier": 1,
        "channel": "official_newsroom",
        "collection_mode": "anthropic_news",
        "url": "https://www.anthropic.com/news",
        "max_results": 30,
        "topics": ["claude", "products", "research"],
    }
    source.update(overrides)
    return source


class AnthropicNewsTests(unittest.TestCase):
    def test_parses_and_deduplicates_official_news(self):
        signals = parse_anthropic_news(HTML_FIXTURE, make_source())

        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0]["company"], "Anthropic")
        self.assertEqual(signals[0]["platform"], "official")
        self.assertEqual(signals[0]["published_at"], "2026-07-27T00:00:00+00:00")
        self.assertEqual(
            signals[0]["canonical_url"],
            "https://www.anthropic.com/news/claude-opus-example",
        )
        self.assertIn("long-running agents", signals[0]["summary"])
        self.assertEqual(signals[0]["confidence"], 0.98)

    def test_list_item_without_summary_uses_honest_fallback(self):
        signals = parse_anthropic_news(HTML_FIXTURE, make_source())
        signal = next(item for item in signals if "open models" in item["title"])

        self.assertIn("Anthropic Newsroom 发布", signal["summary"])
        self.assertIn("Announcements", signal["summary"])

    def test_collector_accepts_injected_fetcher(self):
        signals = collect_anthropic_news(
            make_source(max_results=1),
            fetcher=lambda _url: HTML_FIXTURE,
        )

        self.assertEqual(len(signals), 1)

    def test_rejects_non_anthropic_news_source(self):
        with self.assertRaisesRegex(ValueError, "not an Anthropic News source"):
            collect_anthropic_news(
                make_source(collection_mode="rss"),
                fetcher=lambda _url: HTML_FIXTURE,
            )

    def test_rejects_invalid_limit(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            parse_anthropic_news(HTML_FIXTURE, make_source(max_results=0))


if __name__ == "__main__":
    unittest.main()
