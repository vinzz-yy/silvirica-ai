from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.repository.detector import ProjectDetector


class TestProjectDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_detect_python_project(self) -> None:
        (self.root / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
        (self.root / "main.py").write_text("print('hello')", encoding="utf-8")

        detector = ProjectDetector(self.root)
        info = detector.detect()

        self.assertIn("Python", info["languages"])
        self.assertIn("pip/poetry", info["package_managers"])

    def test_detect_laravel_project(self) -> None:
        (self.root / "artisan").write_text("#!/usr/bin/env php\n", encoding="utf-8")
        (self.root / "composer.json").write_text('{"name": "test/laravel"}', encoding="utf-8")

        detector = ProjectDetector(self.root)
        info = detector.detect()

        self.assertIn("PHP", info["languages"])
        self.assertIn("Laravel", info["frameworks"])
        self.assertIn("composer", info["package_managers"])

    def test_detect_react_project(self) -> None:
        (self.root / "package.json").write_text('{"dependencies": {"react": "^18.0.0", "next": "14.0.0"}}', encoding="utf-8")
        (self.root / "App.tsx").write_text("export const App = () => <div>App</div>;", encoding="utf-8")

        detector = ProjectDetector(self.root)
        info = detector.detect()

        self.assertIn("TypeScript", info["languages"])
        self.assertIn("React", info["frameworks"])
        self.assertIn("Next.js", info["frameworks"])
        self.assertIn("npm", info["package_managers"])


if __name__ == "__main__":
    unittest.main()
