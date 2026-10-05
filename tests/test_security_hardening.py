from __future__ import annotations
import shutil
import tempfile
import unittest
from pathlib import Path

from silvirica.context.compiler import SmartContextCompiler
from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.core.config import ProjectConfig
from silvirica.daemon.server import SilviricaDaemonHandler
from silvirica.mcp.tools import MCPToolRegistry
from silvirica.memory.vault import ObsidianMemoryVault


class TestSecurityHardening(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.memory_dir = self.root / ".silvirica" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.vault = ObsidianMemoryVault(self.memory_dir)
        self.mcp = MCPToolRegistry(self.root)

    def tearDown(self) -> None:
        try:
            self.temp_dir.cleanup()
        except Exception:
            shutil.rmtree(self.temp_dir.name, ignore_errors=True)

    def test_mcp_security_path_traversal_blocked(self) -> None:
        # Attempt to scan outside workspace root
        res = self.mcp.call_tool("silvirica_security", {"file_path": "../../../../etc/passwd"})
        self.assertTrue(isinstance(res, list))
        self.assertTrue(len(res) > 0)
        self.assertIn("Access denied", res[0].get("message", ""))

    def test_memory_vault_path_traversal_blocked(self) -> None:
        # Attempt to read/write/delete outside memory_dir
        self.assertIsNone(self.vault.read_note("../../escape_test"))
        self.assertFalse(self.vault.delete_note("../../../etc/shadow"))

    def test_daemon_origin_validation(self) -> None:
        handler = SilviricaDaemonHandler
        self.assertTrue(handler._is_origin_allowed("http://localhost:3000"))
        self.assertTrue(handler._is_origin_allowed("http://127.0.0.1:8080"))
        self.assertTrue(handler._is_origin_allowed("vscode-webview://panel"))
        self.assertFalse(handler._is_origin_allowed("https://malicious-site.com"))
        self.assertFalse(handler._is_origin_allowed("http://evil-attacker.io"))

    def test_prompt_injection_boundary_directive(self) -> None:
        compiler = SmartContextCompiler(ProjectConfig())
        bundle = compiler.compile(task="Review authentication middleware")
        self.assertIn("# SYSTEM SECURITY DIRECTIVE", bundle.prompt)
        self.assertIn("UNTRUSTED DATA", bundle.prompt)

    def test_high_entropy_secret_redaction(self) -> None:
        # 48-character high-entropy random hex token
        high_entropy_token = "4f8a91b2c3d4e5f67890abcdef1234567890abcdef123456"
        text = f"const SECRET_VAR = '{high_entropy_token}';"

        # Test in Balanced mode
        redacted_balanced, count_b = SecretRedactor.redact(text, mode=SecurityMode.BALANCED)
        self.assertNotIn(high_entropy_token, redacted_balanced)
        self.assertTrue(count_b >= 1)

        # Test in Strict mode
        redacted_strict, count_s = SecretRedactor.redact(text, mode=SecurityMode.STRICT)
        self.assertNotIn(high_entropy_token, redacted_strict)
        self.assertTrue(count_s >= 1)


if __name__ == "__main__":
    unittest.main()
