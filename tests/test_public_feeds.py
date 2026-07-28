import unittest

from tools.public_feeds import collect_public_feed, parse_public_feed


ATOM_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Agent memory discussion</title>
    <updated>2026-07-28T02:00:00Z</updated>
    <link rel="alternate" href="https://www.reddit.com/r/example/comments/123"/>
    <content type="html">&lt;p&gt;Developers compare recovery patterns.&lt;/p&gt;</content>
  </entry>
</feed>
"""

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>New agent release</title>
      <link>https://example.com/releases/agent</link>
      <pubDate>Tue, 28 Jul 2026 02:00:00 GMT</pubDate>
      <description>&lt;p&gt;The official release adds durable state.&lt;/p&gt;</description>
    </item>
  </channel>
</rss>
"""


def make_source(**overrides):
    source = {
        "id": "example_feed",
        "name": "Example updates",
        "company": "Example AI",
        "source_tier": 1,
        "channel": "official",
        "collection_mode": "rss",
        "url": "https://example.com/feed.xml",
        "topics": ["agents"],
    }
    source.update(overrides)
    return source


class PublicFeedsTests(unittest.TestCase):
    def test_parses_atom_community_feed(self):
        signals = parse_public_feed(
            ATOM_FIXTURE,
            make_source(
                name="r/example",
                company="Community",
                source_tier=3,
                channel="reddit",
            ),
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["platform"], "reddit")
        self.assertEqual(signals[0]["source_tier"], 3)
        self.assertEqual(signals[0]["canonical_url"], "https://www.reddit.com/r/example/comments/123")
        self.assertIn("社区早期信号", signals[0]["why_it_matters"])

    def test_parses_rss_timestamp_and_content(self):
        signals = parse_public_feed(RSS_FIXTURE, make_source())

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["published_at"], "2026-07-28T02:00:00+00:00")
        self.assertIn("durable state", signals[0]["summary"])
        self.assertEqual(signals[0]["confidence"], 0.9)

    def test_non_official_rss_does_not_claim_official_platform(self):
        signals = parse_public_feed(
            RSS_FIXTURE,
            make_source(source_tier=3, channel="community"),
        )

        self.assertEqual(signals[0]["platform"], "other")

    def test_collector_accepts_injected_fetcher(self):
        signals = collect_public_feed(
            make_source(),
            fetcher=lambda _url: RSS_FIXTURE,
        )

        self.assertEqual(signals[0]["title"], "Example updates · New agent release")

    def test_rejects_non_rss_source(self):
        with self.assertRaisesRegex(ValueError, "not a public RSS/Atom source"):
            collect_public_feed(
                make_source(collection_mode="atom"),
                fetcher=lambda _url: RSS_FIXTURE,
            )


if __name__ == "__main__":
    unittest.main()
