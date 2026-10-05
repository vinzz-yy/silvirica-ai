from __future__ import annotations
import shutil
import tempfile
import unittest
from pathlib import Path
from silvirica.models.outcome import OutcomeEngine, TaskOutcome


class TestOutcomeEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "outcomes.db"
        self.engine = OutcomeEngine(self.db_path)

    def tearDown(self) -> None:
        try:
            self.temp_dir.cleanup()
        except Exception:
            shutil.rmtree(self.temp_dir.name, ignore_errors=True)

    def test_record_and_query_verified_outcomes(self) -> None:
        outcome1 = TaskOutcome(
            task_id="task-1",
            task_type="bug_fix",
            task_description="Fix login bug",
            context_tokens=1200,
            skills_selected=["debugging", "security-audit"],
            model_selected="coding-model",
            tests_passed=10,
            tests_total=10,
            validation_passed=True,
            latency_seconds=1.5,
        )
        self.assertTrue(outcome1.is_verified_success)
        self.engine.record_outcome(outcome1)

        outcome2 = TaskOutcome(
            task_id="task-2",
            task_type="bug_fix",
            task_description="Fix another bug",
            context_tokens=1400,
            skills_selected=["debugging"],
            model_selected="coding-model",
            tests_passed=5,
            tests_total=5,
            validation_passed=True,
            latency_seconds=1.2,
        )
        self.engine.record_outcome(outcome2)

        best_model = self.engine.get_best_model_for_task("bug_fix")
        self.assertEqual(best_model, "coding-model")

        optimal_skills = self.engine.get_optimal_skills_for_task("bug_fix")
        self.assertIn("debugging", optimal_skills)

        stats = self.engine.get_outcome_statistics()
        self.assertEqual(stats["total_tasks"], 2)
        self.assertEqual(stats["success_rate"], 1.0)

    def test_unverified_outcome_rejected(self) -> None:
        failed_outcome = TaskOutcome(
            task_id="task-3",
            task_type="refactor",
            task_description="Refactor database",
            context_tokens=3000,
            skills_selected=["database"],
            model_selected="cheap-model",
            tests_passed=4,
            tests_total=6,  # 2 tests failed!
            validation_passed=True,
            latency_seconds=3.0,
        )
        self.assertFalse(failed_outcome.is_verified_success)
        self.engine.record_outcome(failed_outcome)

        stats = self.engine.get_outcome_statistics()
        self.assertEqual(stats["total_tasks"], 1)
        self.assertEqual(stats["success_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
