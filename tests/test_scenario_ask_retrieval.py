from __future__ import annotations
import shutil
import tempfile
import unittest
from pathlib import Path

from silvirica.cli.ask import execute_ask
from silvirica.core.project import ProjectBrain
from silvirica.graph.graph_db import GraphDatabase
from silvirica.graph.query import GraphQueryEngine
from silvirica.observatory.explain import DecisionExplainer
from silvirica.observatory.telemetry import TelemetryStore
from silvirica.repository.indexer import RepositoryIndexer
from silvirica.repository.symbols import SymbolIndex


class TestScenarioAskRetrieval(unittest.TestCase):
    """
    Integration test reproducing the exact scenario from user request:
    app.py with:
      - calculate_total
      - calculate_discount
      - checkout
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create app.py exactly as specified
        app_code = (
            "def calculate_total(price, quantity):\n"
            "    return price * quantity\n\n"
            "def calculate_discount(total, percent):\n"
            "    return total - (total * percent / 100)\n\n"
            "def checkout(price, quantity, discount):\n"
            "    total = calculate_total(price, quantity)\n"
            "    return calculate_discount(total, discount)\n\n"
            "print(checkout(100, 5, 10))\n"
        )
        (self.root / "app.py").write_text(app_code, encoding="utf-8")

        self.brain = ProjectBrain(self.root)
        self.brain.init()

        self.indexer = RepositoryIndexer(self.root)
        self.index_res = self.indexer.index(force=True)

    def tearDown(self) -> None:
        try:
            self.temp_dir.cleanup()
        except Exception:
            shutil.rmtree(self.temp_dir.name, ignore_errors=True)

    def test_indexing_discovered_all_three_symbols_and_relations(self) -> None:
        # Assert 3 symbols discovered
        sym_idx = SymbolIndex(self.root / ".silvirica" / "symbols" / "symbols.db")
        symbols = sym_idx.find_by_file("app.py")
        sym_names = [s.name for s in symbols]
        self.assertIn("calculate_total", sym_names)
        self.assertIn("calculate_discount", sym_names)
        self.assertIn("checkout", sym_names)
        self.assertEqual(len(symbols), 3)

        # Assert CALLS relationships
        graph_db = GraphDatabase(self.root / ".silvirica" / "graph" / "graph.db")
        engine = GraphQueryEngine(graph_db)
        graph_output = engine.query("checkout")
        self.assertIn("calculate_total", graph_output)
        self.assertIn("calculate_discount", graph_output)

    def test_ask_list_functions_in_app_py(self) -> None:
        query = "What functions exist in app.py? List their exact names."
        ans = execute_ask(self.root, query)

        self.assertIn("calculate_total", ans)
        self.assertIn("calculate_discount", ans)
        self.assertIn("checkout", ans)
        self.assertIn("ZERO-MODEL PATH ACTIVATED", ans)

        # Verify explain-last
        telemetry = TelemetryStore(self.root / ".silvirica" / "metrics" / "telemetry.db")
        explainer = DecisionExplainer(telemetry)
        explanation = explainer.explain_last()

        self.assertIn("Zero-Model Hit:     YES", explanation)
        self.assertIn("Provider Called:    NO", explanation)
        self.assertIn("Actual Model:       NONE", explanation)
        self.assertIn("Files Retrieved:    1", explanation)
        self.assertIn("Symbols Retrieved:  3", explanation)

    def test_ask_where_is_checkout_defined(self) -> None:
        query = "Where is checkout defined?"
        ans = execute_ask(self.root, query)

        self.assertIn("app.py", ans)
        self.assertIn("checkout", ans)
        self.assertIn("ZERO-MODEL PATH ACTIVATED", ans)

        telemetry = TelemetryStore(self.root / ".silvirica" / "metrics" / "telemetry.db")
        explainer = DecisionExplainer(telemetry)
        explanation = explainer.explain_last()

        self.assertIn("Zero-Model Hit:     YES", explanation)
        self.assertIn("Files Retrieved:    1", explanation)
        self.assertTrue(int(telemetry.get_last_decision()["symbols_retrieved"]) >= 1)

    def test_ask_what_does_checkout_call(self) -> None:
        query = "What functions does checkout call?"
        ans = execute_ask(self.root, query)

        self.assertIn("calculate_total", ans)
        self.assertIn("calculate_discount", ans)
        self.assertIn("ZERO-MODEL PATH ACTIVATED", ans)

        telemetry = TelemetryStore(self.root / ".silvirica" / "metrics" / "telemetry.db")
        decision = telemetry.get_last_decision()
        self.assertTrue(decision["zero_model"])
        self.assertFalse(decision["provider_called"])
        self.assertEqual(decision["actual_model"], "NONE")
        self.assertTrue(decision["graph_nodes_used"] >= 2)


if __name__ == "__main__":
    unittest.main()
