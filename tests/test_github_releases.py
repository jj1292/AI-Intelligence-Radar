import unittest

from tools.github_releases import collect_github_releases, parse_github_releases_atom


ATOM_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Release notes</title>
  <entry>
    <id>tag:github.com,2008:example/v1.2.3</id>
    <updated>2026-07-26T08:00:00Z</updated>
    <link rel="alternate" type="text/html" href="https://github.com/example/agent/releases/tag/v1.2.3"/>
    <title>v1.2.3</title>
    <content type="html">&lt;h2&gt;What's changed&lt;/h2&gt;&lt;ul&gt;&lt;li&gt;Improved checkpoint recovery&lt;/li&gt;&lt;/ul&gt;</content>
  </entry>
</feed>
"""

EARLY_RELEASE_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <updated>2026-07-27T08:00:00Z</updated>
    <link rel="alternate" href="https://github.com/example/agent/releases/tag/v2.0.0-alpha.4"/>
    <title>v2.0.0-alpha.4</title>
    <content type="html">Experimental build.</content>
  </entry>
  <entry>
    <updated>2026-07-26T08:00:00Z</updated>
    <link rel="alternate" href="https://github.com/example/agent/releases/tag/v1.3.0"/>
    <title>v1.3.0</title>
    <content type="html">Stable release.</content>
  </entry>
</feed>
"""


def make_source():
    return {
        "id": "example_releases",
        "name": "example/agent releases",
        "company": "Example AI",
        "source_tier": 1,
        "channel": "official_repository",
        "collection_mode": "atom",
        "url": "https://github.com/example/agent/releases.atom",
        "status": "ready",
        "topics": ["agents", "reliability"],
    }


class GithubReleasesTests(unittest.TestCase):
    def test_parses_atom_entry_into_signal_contract(self):
        signals = parse_github_releases_atom(ATOM_FIXTURE, make_source())
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["company"], "Example AI")
        self.assertEqual(signals[0]["platform"], "github")
        self.assertEqual(signals[0]["source_tier"], 1)
        self.assertIn("checkpoint recovery", signals[0]["summary"])
        self.assertEqual(
            signals[0]["canonical_url"],
            "https://github.com/example/agent/releases/tag/v1.2.3",
        )

    def test_collector_accepts_injected_fetcher(self):
        signals = collect_github_releases(make_source(), fetcher=lambda _: ATOM_FIXTURE)
        self.assertEqual(signals[0]["title"], "Example AI · v1.2.3")

    def test_keeps_early_builds_out_of_important_signal_tier(self):
        signals = parse_github_releases_atom(EARLY_RELEASE_FIXTURE, make_source())

        self.assertEqual(signals[0]["impact_score"], 1)
        self.assertIn("早期构建", signals[0]["why_it_matters"])
        self.assertEqual(signals[1]["impact_score"], 3)
        self.assertIn("稳定发布", signals[1]["why_it_matters"])

    def test_rejects_non_atom_source(self):
        source = make_source() | {"collection_mode": "official_web"}
        with self.assertRaises(ValueError):
            collect_github_releases(source, fetcher=lambda _: ATOM_FIXTURE)


if __name__ == "__main__":
    unittest.main()
