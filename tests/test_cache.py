from __future__ import annotations
import tempfile
import time
import unittest
from pathlib import Path
from silvirica.cache.engine import CacheTier, MultiTierCacheManager


class TestMultiTierCache(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)
        self.cache = MultiTierCacheManager(self.cache_dir, default_ttl_seconds=60)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cache_set_and_get(self) -> None:
        key = MultiTierCacheManager.generate_key(CacheTier.L1_REQUEST, "where is AuthController")
        data = {"answer": "Found in app/AuthController.php", "zero_model": True}

        self.cache.set(CacheTier.L1_REQUEST, key, data, project_state_hash="hash123")
        retrieved = self.cache.get(CacheTier.L1_REQUEST, key, current_state_hash="hash123")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["answer"], "Found in app/AuthController.php")

    def test_cache_miss_on_state_change(self) -> None:
        key = MultiTierCacheManager.generate_key(CacheTier.L1_REQUEST, "where is AuthController")
        data = {"answer": "Found in app/AuthController.php"}

        self.cache.set(CacheTier.L1_REQUEST, key, data, project_state_hash="hash123")
        # Query with different state hash
        retrieved = self.cache.get(CacheTier.L1_REQUEST, key, current_state_hash="hash999")
        self.assertIsNone(retrieved)

    def test_cache_invalidation_by_state(self) -> None:
        key1 = MultiTierCacheManager.generate_key(CacheTier.L2_SYMBOL, "User")
        key2 = MultiTierCacheManager.generate_key(CacheTier.L2_SYMBOL, "Post")

        self.cache.set(CacheTier.L2_SYMBOL, key1, {"symbol": "User"}, project_state_hash="old_state")
        self.cache.set(CacheTier.L2_SYMBOL, key2, {"symbol": "Post"}, project_state_hash="new_state")

        invalidated = self.cache.invalidate_state(current_state_hash="new_state")
        self.assertTrue(invalidated >= 1)

        self.assertIsNone(self.cache.get(CacheTier.L2_SYMBOL, key1, current_state_hash="new_state"))
        self.assertIsNotNone(self.cache.get(CacheTier.L2_SYMBOL, key2, current_state_hash="new_state"))

    def test_cache_stats(self) -> None:
        key = MultiTierCacheManager.generate_key(CacheTier.L5_MEMORY, "login")
        self.cache.get(CacheTier.L5_MEMORY, key)  # Miss
        self.cache.set(CacheTier.L5_MEMORY, key, {"record": "ADR 1"})
        self.cache.get(CacheTier.L5_MEMORY, key)  # Hit

        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate_percentage"], 50.0)


if __name__ == "__main__":
    unittest.main()
