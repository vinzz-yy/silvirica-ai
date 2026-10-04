from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.core.types import ComplexityLevel, RiskLevel, SymbolInfo, SymbolKind
from silvirica.fastgate.classifier import TaskClassifier
from silvirica.fastgate.gate import FastGate
from silvirica.fastgate.zero_model import ZeroModelResolver
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.repository.symbols import SymbolIndex


class TestFastGate(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.symbols_db = self.root / "symbols.db"
        self.index = SymbolIndex(self.symbols_db)
        self.vault = ObsidianMemoryVault(self.root / "memory")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_task_classification_instant(self) -> None:
        clf = TaskClassifier.classify("Center this button with css")
        self.assertEqual(clf["complexity"], ComplexityLevel.LEVEL_0_INSTANT)
        self.assertEqual(clf["risk"], RiskLevel.SAFE)

    def test_task_classification_critical(self) -> None:
        clf = TaskClassifier.classify("Check if tenants can access each other's financial records via IDOR")
        self.assertEqual(clf["complexity"], ComplexityLevel.LEVEL_5_CRITICAL)
        self.assertEqual(clf["risk"], RiskLevel.CRITICAL)

    def test_zero_model_resolution(self) -> None:
        # Save a symbol
        sym = SymbolInfo(
            name="AuthController",
            kind=SymbolKind.CLASS,
            file_path="app/Http/Controllers/AuthController.php",
            start_line=12,
            end_line=95,
        )
        self.index.save_symbols("app/Http/Controllers/AuthController.php", [sym])

        result = ZeroModelResolver.try_resolve("Where is AuthController?", self.root, self.index, self.vault)
        self.assertIsNotNone(result)
        self.assertIn("app/Http/Controllers/AuthController.php", result)

    def test_fast_gate_evaluation(self) -> None:
        decision = FastGate.evaluate(
            query="Where is AuthController?",
            root_path=self.root,
            symbol_index=self.index,
            memory_vault=self.vault,
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision.complexity, ComplexityLevel.LEVEL_0_INSTANT)


if __name__ == "__main__":
    unittest.main()
