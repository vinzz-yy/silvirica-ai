from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.core.types import FindingSeverity
from silvirica.security.engine import SecurityEngine
from silvirica.security.rules import scan_code_for_vulnerabilities
from silvirica.security.secret_scanner import SecretScanner


class TestSecurityEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_detect_hardcoded_secrets(self) -> None:
        secret_file = self.root / "config.py"
        secret_file.write_text("AWS_SECRET = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")

        findings = SecretScanner.scan_file(secret_file, "config.py")
        self.assertTrue(len(findings) >= 1)
        self.assertEqual(findings[0].severity, FindingSeverity.CRITICAL)

    def test_detect_sql_injection(self) -> None:
        vulnerable_code = """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
"""
        findings = scan_code_for_vulnerabilities(vulnerable_code, "db.py")
        self.assertTrue(any("SQL" in f.title or "SQL" in f.rule_id for f in findings))

    def test_detect_command_injection(self) -> None:
        vulnerable_code = """
import os
def run_cmd(user_input):
    os.system("ping " + user_input)
"""
        findings = scan_code_for_vulnerabilities(vulnerable_code, "cmd.py")
        self.assertTrue(any("Command" in f.title or "CMD" in f.rule_id for f in findings))

    def test_security_engine_full_scan(self) -> None:
        (self.root / "safe.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
        (self.root / "vuln.py").write_text("eval(user_data)\n", encoding="utf-8")

        engine = SecurityEngine(self.root)
        report = engine.scan_repository()

        self.assertEqual(report["files_scanned"], 2)
        self.assertTrue(report["total_findings"] >= 1)


if __name__ == "__main__":
    unittest.main()
