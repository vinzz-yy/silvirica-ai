from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from silvirica.cli.ask import execute_ask
from silvirica.core.project import ProjectBrain
from silvirica.observatory.explain import explain_last
from silvirica.repository.indexer import RepositoryIndexer


class TestCacheRegression(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.brain = ProjectBrain(self.root)
        self.brain.init()

        # Write initial app.py
        self.app_py = self.root / "app.py"
        self.app_py.write_text(
            "def calculate_total(price, quantity):\n"
            "    return price * quantity\n\n"
            "def checkout(price, quantity):\n"
            "    return calculate_total(price, quantity)\n",
            encoding="utf-8",
        )
        RepositoryIndexer(self.root).index()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cache_miss_then_hit_then_invalidation_on_code_change(self) -> None:
        query = "What functions exist in app.py? List their exact names."

        # 1. First Ask -> Cache MISS
        res1 = execute_ask(self.root, query)
        self.assertIn("calculate_total", res1)
        self.assertIn("checkout", res1)

        exp1 = explain_last(self.root)
        self.assertIn("Cache Status:       MISS", exp1)

        # 2. Second Ask (identical query, unmodified code) -> Cache HIT
        res2 = execute_ask(self.root, query)
        self.assertIn("calculate_total", res2)
        self.assertIn("checkout", res2)

        exp2 = explain_last(self.root)
        self.assertIn("Cache Status:       HIT", exp2)

        # 3. Modify app.py -> add calculate_discount
        self.app_py.write_text(
            "def calculate_total(price, quantity):\n"
            "    return price * quantity\n\n"
            "def calculate_discount(total, percent):\n"
            "    return total - (total * percent / 100)\n\n"
            "def checkout(price, quantity, discount):\n"
            "    total = calculate_total(price, quantity)\n"
            "    return calculate_discount(total, discount)\n",
            encoding="utf-8",
        )
        # Re-analyze to update AST index and state hash
        RepositoryIndexer(self.root).index()

        # 4. Third Ask -> State hash changed, stale cache must NOT be used
        res3 = execute_ask(self.root, query)
        self.assertIn("calculate_discount", res3)
        self.assertIn("calculate_total", res3)
        self.assertIn("checkout", res3)

        exp3 = explain_last(self.root)
        self.assertIn("Cache Status:       MISS", exp3)


if __name__ == "__main__":
    unittest.main()
