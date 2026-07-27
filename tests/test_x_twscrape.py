import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from tools.x_twscrape import (
    _setup_account,
    collect_x_posts_async,
    load_since_id,
    normalize_x_tweet,
)


def make_source(**overrides):
    source = {
        "id": "x_frontier_ai_accounts",
        "name": "Frontier AI official X accounts",
        "company": "Multiple",
        "source_tier": 2,
        "collection_mode": "x_twscrape",
        "query": "from:OpenAI -is:retweet -is:reply has:links",
        "max_results": 100,
        "author_companies": {"OpenAI": "OpenAI"},
        "topics": ["models", "agents"],
    }
    source.update(overrides)
    return source


def make_tweet(
    tweet_id=123,
    *,
    username="OpenAI",
    content="A new model and system card are available. https://example.com/model",
):
    return SimpleNamespace(
        id=tweet_id,
        user=SimpleNamespace(username=username),
        rawContent=content,
        url=f"https://x.com/{username}/status/{tweet_id}",
        date=datetime(2026, 7, 27, 2, 0, tzinfo=timezone.utc),
    )


class XTwscrapeTests(unittest.IsolatedAsyncioTestCase):
    def test_normalizes_tweet_and_maps_author_company(self):
        signal = normalize_x_tweet(
            make_tweet(),
            make_source(),
            retrieved_at=datetime(2026, 7, 27, 3, 0, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(signal)
        self.assertEqual(signal["company"], "OpenAI")
        self.assertEqual(signal["author"], "@OpenAI")
        self.assertEqual(signal["source_tier"], 2)
        self.assertEqual(signal["external_id"], "123")
        self.assertLessEqual(len(signal["summary"]), 400)
        self.assertLessEqual(len(signal["evidence"][0]), 240)

    def test_author_mapping_is_case_insensitive(self):
        signal = normalize_x_tweet(make_tweet(username="openai"), make_source())
        self.assertEqual(signal["company"], "OpenAI")

    async def test_filters_old_posts_and_defers_checkpoint_until_commit(self):
        async def fetcher(_query, _database, _limit):
            return [make_tweet(101), make_tweet(100), make_tweet(99)]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "checkpoints" / "x.json"
            checkpoint.parent.mkdir()
            checkpoint.write_text('{"since_id": "100"}\n', encoding="utf-8")

            batch = await collect_x_posts_async(
                make_source(),
                fetcher=fetcher,
                account_db=root / "accounts.db",
                checkpoint_path=checkpoint,
            )

            self.assertEqual([signal["external_id"] for signal in batch.signals], ["101"])
            self.assertEqual(load_since_id(checkpoint), 100)
            self.assertIsNotNone(batch.commit_checkpoint)
            batch.commit_checkpoint()
            self.assertEqual(load_since_id(checkpoint), 101)

    async def test_does_not_create_checkpoint_when_there_are_no_new_valid_posts(self):
        async def fetcher(_query, _database, _limit):
            return [make_tweet(100), make_tweet(99)]

        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "x.json"
            checkpoint.write_text('{"since_id": "100"}\n', encoding="utf-8")
            batch = await collect_x_posts_async(
                make_source(),
                fetcher=fetcher,
                checkpoint_path=checkpoint,
            )

            self.assertEqual(batch.signals, [])
            self.assertIsNone(batch.commit_checkpoint)
            self.assertEqual(load_since_id(checkpoint), 100)

    async def test_rejects_non_x_source_and_invalid_limit(self):
        async def fetcher(_query, _database, _limit):
            return []

        with self.assertRaisesRegex(ValueError, "not a twscrape source"):
            await collect_x_posts_async(make_source(collection_mode="atom"), fetcher=fetcher)
        with self.assertRaisesRegex(ValueError, "between 1 and 500"):
            await collect_x_posts_async(make_source(max_results=0), fetcher=fetcher)

    async def test_setup_requires_explicit_replace_for_existing_account(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "accounts.db"
            cookies = "auth_token=test-token; ct0=test-csrf"

            self.assertTrue(await _setup_account("radar-test", database, cookies))
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                await _setup_account("radar-test", database, cookies)
            self.assertTrue(
                await _setup_account("radar-test", database, cookies, replace=True)
            )

    def test_rejects_corrupt_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "x.json"
            checkpoint.write_text(json.dumps({"since_id": "not-a-number"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid X checkpoint"):
                load_since_id(checkpoint)


if __name__ == "__main__":
    unittest.main()
