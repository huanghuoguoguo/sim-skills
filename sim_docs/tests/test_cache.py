"""Unit tests for sim_docs cache module."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from sim_docs.cache import DocumentCache, CacheEntry, CacheStats


class TestCacheStats(unittest.TestCase):
    """Tests for CacheStats dataclass."""

    def test_default_values(self):
        stats = CacheStats()
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)
        self.assertEqual(stats.size, 0)
        self.assertEqual(stats.max_size, 0)

    def test_custom_values(self):
        stats = CacheStats(hits=10, misses=5, size=3, max_size=32)
        self.assertEqual(stats.hits, 10)
        self.assertEqual(stats.misses, 5)
        self.assertEqual(stats.size, 3)
        self.assertEqual(stats.max_size, 32)


class TestCacheEntry(unittest.TestCase):
    """Tests for CacheEntry dataclass."""

    def test_entry_creation(self):
        entry = CacheEntry(facts={"test": "data"}, mtime=123.45, path="/tmp/test.docx")
        self.assertEqual(entry.facts, {"test": "data"})
        self.assertEqual(entry.mtime, 123.45)
        self.assertEqual(entry.path, "/tmp/test.docx")


class TestDocumentCache(unittest.TestCase):
    """Tests for DocumentCache class."""

    def test_init(self):
        cache = DocumentCache(max_size=16)
        self.assertEqual(cache._stats.max_size, 16)

    def test_get_returns_none_for_missing(self):
        cache = DocumentCache()
        result = cache.get("/nonexistent/path.docx")
        self.assertIsNone(result)

    def test_set_and_get(self):
        cache = DocumentCache()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            facts = {"paragraphs": [{"text": "test"}]}
            cache.set(temp_path, facts)
            result = cache.get(temp_path)
            self.assertEqual(result, facts)
            self.assertEqual(cache.stats().hits, 1)
        finally:
            os.unlink(temp_path)

    def test_mtime_invalidation(self):
        cache = DocumentCache()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            facts = {"paragraphs": [{"text": "test"}]}
            cache.set(temp_path, facts)

            # Modify file
            time.sleep(0.1)  # Ensure mtime changes
            with open(temp_path, "w") as f:
                f.write("modified")

            result = cache.get(temp_path)
            self.assertIsNone(result)  # Should be invalidated
            self.assertEqual(cache.stats().misses, 1)
        finally:
            os.unlink(temp_path)

    def test_lru_eviction(self):
        cache = DocumentCache(max_size=2)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f1:
            f1.write(b"file1")
            path1 = f1.name
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f2:
            f2.write(b"file2")
            path2 = f2.name
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f3:
            f3.write(b"file3")
            path3 = f3.name

        try:
            cache.set(path1, {"id": 1})
            cache.set(path2, {"id": 2})
            self.assertEqual(cache.stats().size, 2)

            # Adding third should evict first (LRU)
            cache.set(path3, {"id": 3})
            self.assertEqual(cache.stats().size, 2)
            self.assertIsNone(cache.get(path1))  # path1 evicted
            self.assertEqual(cache.get(path2), {"id": 2})
            self.assertEqual(cache.get(path3), {"id": 3})
        finally:
            os.unlink(path1)
            os.unlink(path2)
            os.unlink(path3)

    def test_clear(self):
        cache = DocumentCache()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            cache.set(temp_path, {"test": "data"})
            self.assertEqual(cache.stats().size, 1)

            cache.clear()
            self.assertEqual(cache.stats().size, 0)
            self.assertIsNone(cache.get(temp_path))
        finally:
            os.unlink(temp_path)

    def test_stats(self):
        cache = DocumentCache()
        stats = cache.stats()
        self.assertIsInstance(stats, CacheStats)


if __name__ == "__main__":
    unittest.main()