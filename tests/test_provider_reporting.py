from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from silvirica.cli.ask import execute_ask
from silvirica.cli.doctor import SilviricaDoctor
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.project import ProjectBrain
from silvirica.models.router import ModelRouter
from silvirica.observatory.explain import explain_last
from silvirica.repository.indexer import RepositoryIndexer


class TestProviderReporting(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.brain = ProjectBrain(self.root)
        self.brain.init()

        # Create sample project file
        self.app_py = self.root / "app.py"
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
        RepositoryIndexer(self.root).index()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_doctor_reports_local_fallback_when_no_api_key(self) -> None:
        doctor = SilviricaDoctor(self.root)
        report = doctor.run_diagnostics()
        ai_check = report.get("AI Provider")
        self.assertIsNotNone(ai_check)
        self.assertIn("Local Deterministic Fallback Mode active", ai_check["detail"])

    def test_zero_model_reporting_truthfulness(self) -> None:
        query = "What functions exist in app.py? List their exact names."
        result = execute_ask(self.root, query)
        self.assertIn("Provider Called: NO", result)
        self.assertIn("Actual Model: NONE", result)
        self.assertIn("ZERO-MODEL PATH ACTIVATED", result)

        explanation = explain_last(self.root)
        self.assertIn("Zero-Model Hit:     YES (Deterministic Local Engine)", explanation)
        self.assertIn("Provider Called:    NO", explanation)
        self.assertIn("Actual Model:       NONE", explanation)

    def test_fallback_reporting_truthfulness(self) -> None:
        # A query that requires reasoning / non-zero model
        query = "Design a distributed payment processing architecture with idempotency and retry queues."
        result = execute_ask(self.root, query)
        self.assertIn("LOCAL DETERMINISTIC FALLBACK", result)
        self.assertIn("Provider Called: NO", result)
        self.assertIn("Actual Model: NONE", result)

        explanation = explain_last(self.root)
        self.assertIn("Zero-Model Hit:     NO", explanation)
        self.assertIn("Provider Called:    NO", explanation)
        self.assertIn("Actual Model:       NONE", explanation)
        self.assertIn("Fallback Used:      YES", explanation)

    def test_simulated_provider_reporting_when_provider_called(self) -> None:
        with patch.object(
            ModelRouter,
            "execute_routing",
            return_value={
                "text": "Simulated AI Provider Answer",
                "tokens": 42,
                "input_tokens": 120,
                "output_tokens": 42,
                "model": "gpt-4o-mini",
                "selected_model": "gpt-4o-mini",
                "actual_model": "gpt-4o-mini",
                "provider_called": True,
                "provider_available": True,
                "actual_provider": "OpenAICompatible",
                "fallback_used": False,
                "cache_hit": False,
            },
        ):
            query = "Explain how distributed payment processing works."
            result = execute_ask(self.root, query)
            self.assertIn("Provider Called: YES", result)
            self.assertIn("Model: gpt-4o-mini", result)

            explanation = explain_last(self.root)
            self.assertIn("Provider Called:    YES", explanation)
            self.assertIn("Actual Model:       gpt-4o-mini", explanation)
            self.assertIn("Fallback Used:      NO", explanation)


if __name__ == "__main__":
    unittest.main()
