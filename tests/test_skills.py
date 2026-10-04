from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.skills.loader import SkillLoader
from silvirica.skills.progressive import ProgressiveSkillManager


class TestProgressiveSkills(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skills_dir = Path(self.temp_dir.name)
        self.loader = SkillLoader(self.skills_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_builtin_skills_loading(self) -> None:
        skills = self.loader.list_available_skills()
        self.assertTrue(len(skills) >= 10)

        names = [s.name for s in skills]
        self.assertIn("security-audit", names)
        self.assertIn("ui-ux-pro", names)
        self.assertIn("debugging", names)
        self.assertIn("coding-core", names)

    def test_skill_matching(self) -> None:
        matched = self.loader.match_skills("Audit authentication for SQL injection and XSS")
        self.assertIn("security-audit", matched)

        ui_matched = self.loader.match_skills("Align button typography and CSS spacing for mobile")
        self.assertIn("ui-ux-pro", ui_matched)

    def test_progressive_loading_levels(self) -> None:
        level0 = ProgressiveSkillManager.get_level0_metadata(self.loader)
        self.assertTrue(len(level0) >= 10)

        level1 = ProgressiveSkillManager.get_level1_summaries(self.loader, ["security-audit", "debugging"])
        self.assertIn("security-audit", level1)
        self.assertIn("debugging", level1)

        level2 = ProgressiveSkillManager.get_level2_full_instructions(self.loader, ["security-audit"])
        self.assertIn("OWASP", level2)


if __name__ == "__main__":
    unittest.main()
