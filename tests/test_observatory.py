from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.core.types import ComplexityLevel, RoutingCategory, TelemetryEvent
from silvirica.observatory.dashboard import ObservatoryDashboard
from silvirica.observatory.explain import DecisionExplainer
from silvirica.observatory.metrics import ImprovementScoreCalculator
from silvirica.observatory.telemetry import TelemetryStore


class TestObservatory(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "telemetry.db"
        self.store = TelemetryStore(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_record_and_summarize_telemetry(self) -> None:
        event = TelemetryEvent(
            query="Test query",
            complexity=ComplexityLevel.LEVEL_1_SIMPLE,
            category=RoutingCategory.QUICK,
            model_used="gpt-4o-mini",
            input_tokens=500,
            output_tokens=150,
            estimated_baseline_tokens=5000,
            tokens_saved=4500,
            latency_seconds=0.12,
            cache_hit=False,
            zero_model=False,
            skills_activated=["coding-core"],
            files_retrieved=2,
            symbols_retrieved=4,
        )
        self.store.record_event(event)

        summary = self.store.get_summary()
        self.assertEqual(summary["total_queries"], 1)
        self.assertEqual(summary["total_tokens_saved"], 4500)
        self.assertEqual(summary["savings_percentage"], 90.0)

        score_data = ImprovementScoreCalculator.calculate_score(summary)
        self.assertTrue(score_data["overall_score"] > 50)

    def test_decision_explainer(self) -> None:
        explainer = DecisionExplainer(self.store)
        text = explainer.explain_last()
        self.assertIn("No previous decisions", text)

        event = TelemetryEvent(
            query="Explain test",
            complexity=ComplexityLevel.LEVEL_2_STANDARD,
            category=RoutingCategory.STANDARD,
            model_used="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=200,
            estimated_baseline_tokens=10000,
            tokens_saved=9000,
            latency_seconds=0.25,
            cache_hit=True,
            zero_model=False,
        )
        details = {
            "query": "Explain test",
            "complexity": "LEVEL_2_STANDARD",
            "intent": "code_refactoring",
            "risk": "SAFE",
            "zero_model": False,
            "category": "STANDARD",
            "model": "gpt-4o-mini",
            "input_tokens": 1000,
            "estimated_baseline": 10000,
            "reduction_percentage": 90.0,
            "latency_seconds": 0.25,
            "routing_reason": "Optimal model for standard refactoring.",
        }
        self.store.record_event(event, details)

        explained = explainer.explain_last()
        self.assertIn("SILVIRICA DECISION EXPLANATION", explained)
        self.assertIn("Optimal model for standard refactoring", explained)


if __name__ == "__main__":
    unittest.main()
