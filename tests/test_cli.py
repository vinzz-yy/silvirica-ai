from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.benchmark.harness import BenchmarkHarness
from silvirica.benchmark.report import BenchmarkReporter
from silvirica.cli.doctor import SilviricaDoctor
from silvirica.cli.status import show_status
from silvirica.core.project import ProjectBrain
from silvirica.observatory.dashboard import ObservatoryDashboard
from silvirica.repository.indexer import RepositoryIndexer


class TestCLIAndCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.brain = ProjectBrain(self.root)
        self.brain.init()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_silvirica_doctor(self) -> None:
        doctor = SilviricaDoctor(self.root)
        report = doctor.run_diagnostics()
        self.assertTrue(len(report) >= 10)
        self.assertEqual(report["Core Engine"]["status"], "OK")
        self.assertEqual(report["Configuration"]["status"], "OK")

    def test_repository_indexing(self) -> None:
        (self.root / "app.py").write_text("class App:\n    def run(self):\n        pass\n", encoding="utf-8")
        indexer = RepositoryIndexer(self.root)
        res = indexer.index(force=True)
        self.assertTrue(res["symbols_indexed"] >= 2)

    def test_benchmark_harness(self) -> None:
        (self.root / "auth.py").write_text("class AuthController:\n    def login(self):\n        pass\n", encoding="utf-8")
        indexer = RepositoryIndexer(self.root)
        indexer.index(force=True)

        harness = BenchmarkHarness(self.root)
        results = harness.run_all()
        self.assertTrue(len(results) >= 3)

        rendered = BenchmarkReporter.render(results)
        self.assertIn("SILVIRICA AI BENCHMARK SCOREBOARD", rendered)
        self.assertIn("OVERALL TOKEN REDUCTION", rendered)

    def test_dashboard_render(self) -> None:
        dash = ObservatoryDashboard(self.root)
        rendered = dash.render()
        self.assertIn("SILVIRICA AI OBSERVATORY DASHBOARD", rendered)
        self.assertIn("Tech Stack", rendered)


if __name__ == "__main__":
    unittest.main()
