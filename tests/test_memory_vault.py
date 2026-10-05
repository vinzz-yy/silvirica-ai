from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.memory.vault import ObsidianMemoryVault


class TestMemoryVault(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_dir = Path(self.temp_dir.name)
        self.vault = ObsidianMemoryVault(self.mem_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_vault_categories_and_summary(self) -> None:
        summary = self.vault.get_vault_summary()
        self.assertTrue(summary["total_notes"] >= 5)
        self.assertIn("decisions", summary["categories"])

    def test_write_and_search_scored_memory(self) -> None:
        self.vault.write_note(
            name="auth_decisions",
            content="# Auth Architecture\n\n### ADR 001: JWT Authentication\nAdopted stateless JWT tokens.",
            tags=["auth", "security", "jwt"],
        )

        matches = self.vault.search("JWT Authentication")
        self.assertTrue(len(matches) >= 1)
        self.assertEqual(matches[0].id, "auth_decisions")

    def test_backlinks(self) -> None:
        self.vault.write_note(
            name="system_overview",
            content="# System\n\nSee [[auth_decisions]] and [[database_conventions]].",
        )

        backlinks = self.vault.get_backlinks("auth_decisions")
        self.assertIn("system_overview", backlinks)


if __name__ == "__main__":
    unittest.main()
