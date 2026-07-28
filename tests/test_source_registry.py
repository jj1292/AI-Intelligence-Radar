import json
import tempfile
import unittest
from pathlib import Path

from source_registry import expand_subscriptions, load_source_registry


def make_config():
    return {
        "version": 1,
        "github_releases": [
            {
                "repo": "example/agent",
                "company": "Example AI",
                "topics": ["agents"],
            }
        ],
        "rss_feeds": [
            {
                "name": "Example updates",
                "url": "https://example.com/feed.xml",
                "company": "Example AI",
                "topics": ["updates"],
            }
        ],
        "reddit": {
            "communities": ["LocalLLaMA", "MachineLearning"],
            "topics": ["open-models", "community-feedback"],
            "max_results": 20,
        },
        "x": {
            "enabled": True,
            "accounts": [
                {"username": "@ExampleAI", "company": "Example AI"},
                {"username": "ExampleDevs", "company": "Example AI"},
            ],
        },
    }


class SourceRegistryTests(unittest.TestCase):
    def test_expands_human_editable_subscriptions(self):
        sources = expand_subscriptions(make_config())

        self.assertEqual(
            [source["collection_mode"] for source in sources],
            ["atom", "rss", "rss", "x_twscrape"],
        )
        self.assertEqual(
            sources[0]["url"],
            "https://github.com/example/agent/releases.atom",
        )
        self.assertEqual(
            sources[2]["url"],
            "https://www.reddit.com/r/LocalLLaMA+MachineLearning/new/.rss?limit=20",
        )
        self.assertIn("from:ExampleAI", sources[3]["query"])
        self.assertIn("-is:retweet", sources[3]["query"])
        self.assertEqual(
            sources[3]["author_companies"]["ExampleDevs"],
            "Example AI",
        )

    def test_disabled_entries_are_not_expanded(self):
        config = make_config()
        config["github_releases"][0]["enabled"] = False
        config["reddit"]["enabled"] = False
        config["x"]["enabled"] = False

        sources = expand_subscriptions(config)

        self.assertEqual([source["id"] for source in sources], ["rss_example_updates"])

    def test_rejects_invalid_friendly_values(self):
        invalid_repository = make_config()
        invalid_repository["github_releases"][0]["repo"] = "not-a-repository"
        with self.assertRaisesRegex(ValueError, "Invalid GitHub repository"):
            expand_subscriptions(invalid_repository)

        invalid_x = make_config()
        invalid_x["x"]["accounts"][0]["username"] = "not a username"
        with self.assertRaisesRegex(ValueError, "Invalid X username"):
            expand_subscriptions(invalid_x)

        invalid_reddit = make_config()
        invalid_reddit["reddit"]["communities"][0] = "not a community"
        with self.assertRaisesRegex(ValueError, "Invalid Reddit community"):
            expand_subscriptions(invalid_reddit)

        unknown_section = make_config() | {"secret_sources": []}
        with self.assertRaisesRegex(ValueError, "Unknown subscription sections"):
            expand_subscriptions(unknown_section)

    def test_loads_repository_subscription_file(self):
        path = Path(__file__).parents[1] / "config" / "subscriptions.json"
        sources = load_source_registry(path)

        self.assertGreaterEqual(len(sources), 6)
        self.assertIn("github_openai_codex_releases", {source["id"] for source in sources})
        self.assertIn("anthropic_newsroom", {source["id"] for source in sources})
        self.assertIn("reddit_selected_communities", {source["id"] for source in sources})
        self.assertIn("x_selected_accounts", {source["id"] for source in sources})

    def test_expands_supported_official_web_adapter(self):
        config = make_config()
        config["official_web"] = [
            {
                "id": "anthropic_newsroom",
                "adapter": "anthropic_news",
                "name": "Anthropic Newsroom",
                "url": "https://www.anthropic.com/news",
                "company": "Anthropic",
                "topics": ["claude"],
            }
        ]

        source = next(
            item for item in expand_subscriptions(config) if item["id"] == "anthropic_newsroom"
        )

        self.assertEqual(source["collection_mode"], "anthropic_news")
        self.assertEqual(source["source_tier"], 1)

    def test_loads_subscription_object_from_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "subscriptions.json"
            path.write_text(json.dumps(make_config()), encoding="utf-8")

            sources = load_source_registry(path)

        self.assertEqual(len(sources), 4)


if __name__ == "__main__":
    unittest.main()
