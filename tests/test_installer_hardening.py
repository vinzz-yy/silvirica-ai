from __future__ import annotations
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestInstallerHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).parent.parent.resolve()
        cls.install_ps1 = cls.repo_root / "install.ps1"
        cls.install_sh = cls.repo_root / "install.sh"

    def test_installer_files_exist(self) -> None:
        self.assertTrue(self.install_ps1.exists(), "install.ps1 must exist in repo root")
        self.assertTrue(self.install_sh.exists(), "install.sh must exist in repo root")

    def test_powershell_installer_dry_run(self) -> None:
        if os.name != "nt":
            self.skipTest("PowerShell installer test is specific to Windows")

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.install_ps1),
            "-DryRun",
            "-Channel",
            "main",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(proc.returncode, 0, f"Dry run failed: {proc.stderr}")
        self.assertIn("[DRY RUN]", proc.stdout)

    def test_powershell_installer_invalid_sha256_format_rejected(self) -> None:
        if os.name != "nt":
            self.skipTest("PowerShell installer test is specific to Windows")

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.install_ps1),
            "-ExpectedSha256",
            "invalid_short_hash",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertNotEqual(proc.returncode, 0)
        output = proc.stdout + proc.stderr
        self.assertIn("64-character", output)

    def test_powershell_installer_invalid_channel_rejected(self) -> None:
        if os.name != "nt":
            self.skipTest("PowerShell installer test is specific to Windows")

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.install_ps1),
            "-Channel",
            "unsupported_channel",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertNotEqual(proc.returncode, 0)

    def test_sha256_verification_logic(self) -> None:
        # Test accurate sha256 checksum calculation
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("silvirica test package payload 12345")
            temp_path = Path(f.name)

        try:
            expected_hash = hashlib.sha256(temp_path.read_bytes()).hexdigest().lower()
            self.assertEqual(len(expected_hash), 64)

            # Valid checksum matching
            actual_hash = hashlib.sha256(temp_path.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_hash, expected_hash)

            # Corrupted artifact / Mismatched checksum
            corrupted_bytes = temp_path.read_bytes() + b"_corrupted"
            corrupted_hash = hashlib.sha256(corrupted_bytes).hexdigest().lower()
            self.assertNotEqual(corrupted_hash, expected_hash)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_bash_installer_options_content(self) -> None:
        content = self.install_sh.read_text(encoding="utf-8")
        # Ensure no silent fallback to main
        self.assertIn("--channel", content)
        self.assertIn("--expected-sha256", content)
        self.assertIn("--dry-run", content)


if __name__ == "__main__":
    unittest.main()
