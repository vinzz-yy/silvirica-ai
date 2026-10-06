from __future__ import annotations
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from silvirica.cli.main import main


class TestCLISmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.old_cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self) -> None:
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def _run_cli(self, args: list[str]) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(args)
        return buf.getvalue()

    def test_full_e2e_cli_workflow(self) -> None:
        # 1. silvirica init
        init_out = self._run_cli(["init"])
        self.assertIn("Project initialized successfully", init_out)

        # 2. silvirica doctor (initial)
        doctor_out = self._run_cli(["doctor"])
        self.assertIn("SILVIRICA AI DOCTOR REPORT", doctor_out)
        self.assertNotIn("[ERROR]", doctor_out)

        # 3. Create app.py with calculate_total, calculate_discount, checkout
        app_py = self.root / "app.py"
        app_py.write_text(
            "def calculate_total(price, quantity):\n"
            "    return price * quantity\n\n"
            "def calculate_discount(total, percent):\n"
            "    return total - (total * percent / 100)\n\n"
            "def checkout(price, quantity, discount):\n"
            "    total = calculate_total(price, quantity)\n"
            "    return calculate_discount(total, discount)\n\n"
            "print(checkout(100, 5, 10))\n",
            encoding="utf-8",
        )

        # 4. silvirica analyze
        analyze_out = self._run_cli(["analyze", "--force"])
        self.assertIn("REPOSITORY INDEX REPORT", analyze_out)
        self.assertIn("symbols_indexed", analyze_out)

        # 5. silvirica status
        status_out = self._run_cli(["status"])
        self.assertIn("SILVIRICA STATUS", status_out)
        self.assertIn("Symbols Indexed:   3", status_out)

        # 6. silvirica ask
        ask_out = self._run_cli(["ask", "What functions exist in app.py? List their exact names."])
        self.assertIn("calculate_total", ask_out)
        self.assertIn("calculate_discount", ask_out)
        self.assertIn("checkout", ask_out)

        # 7. silvirica graph "checkout"
        graph_out = self._run_cli(["graph", "checkout"])
        self.assertIn("calculate_total", graph_out)
        self.assertIn("calculate_discount", graph_out)

        # 8. silvirica explain-last
        explain_out = self._run_cli(["explain-last"])
        self.assertIn("Zero-Model Hit:     YES", explain_out)
        self.assertIn("Provider Called:    NO", explain_out)
        self.assertIn("Actual Model:       NONE", explain_out)
        self.assertIn("Files Retrieved:    1", explain_out)
        self.assertIn("Symbols Retrieved:  3", explain_out)

        # 9. silvirica jev doctor
        jev_doc_out = self._run_cli(["jev", "doctor"])
        self.assertIn("JEV DOCTOR", jev_doc_out)

        # 10. silvirica jev benchmark
        jev_bench_out = self._run_cli(["jev", "benchmark"])
        self.assertIn("BENCHMARK", jev_bench_out)

        # 11. silvirica security
        sec_out = self._run_cli(["security", "scan"])
        self.assertIn("SECURITY INTELLIGENCE AUDIT", sec_out)

        # 12. silvirica benchmark
        bench_out = self._run_cli(["benchmark"])
        self.assertIn("BENCHMARK SCOREBOARD", bench_out)
        self.assertIn("ALL GATES PASSED", bench_out)

        # 13. silvirica doctor (final validation)
        final_doc_out = self._run_cli(["doctor"])
        self.assertIn("SILVIRICA AI DOCTOR REPORT", final_doc_out)
        self.assertNotIn("[ERROR]", final_doc_out)


if __name__ == "__main__":
    unittest.main()
