import unittest

from tools.collection import CollectionBatch
from tools.source_dispatch import SourceDispatcher


class SourceDispatcherTests(unittest.TestCase):
    def test_wraps_legacy_list_collector(self):
        dispatcher = SourceDispatcher()
        dispatcher.register("legacy", lambda _source: [{"id": "one"}])

        batch = dispatcher.collect({"collection_mode": "legacy"})

        self.assertEqual(batch.signals, [{"id": "one"}])
        self.assertIsNone(batch.commit_checkpoint)

    def test_preserves_collection_batch(self):
        commit = lambda: None
        expected = CollectionBatch([{"id": "one"}], commit)
        dispatcher = SourceDispatcher()
        dispatcher.register("batch", lambda _source: expected)

        self.assertIs(dispatcher.collect({"collection_mode": "batch"}), expected)

    def test_rejects_unsupported_mode(self):
        dispatcher = SourceDispatcher()
        with self.assertRaisesRegex(ValueError, "Unsupported collection mode"):
            dispatcher.collect({"collection_mode": "unknown"})


if __name__ == "__main__":
    unittest.main()
