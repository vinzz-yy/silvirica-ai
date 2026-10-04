from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Set


class ProjectDetector:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()

    def detect(self) -> Dict[str, Any]:
        languages = self._detect_languages()
        frameworks = self._detect_frameworks()
        package_managers = self._detect_package_managers()
        databases = self._detect_databases()
        routes_summary = self._detect_routes_structure()
        tests_summary = self._detect_testing_framework()
        has_docker = (self.root_path / "Dockerfile").exists() or (self.root_path / "docker-compose.yml").exists()

        # Cross-enrich languages if frameworks indicate them
        if "Laravel" in frameworks or "Symfony" in frameworks or (self.root_path / "composer.json").exists() or (self.root_path / "artisan").exists():
            languages.add("PHP")
        if (self.root_path / "pyproject.toml").exists() or (self.root_path / "requirements.txt").exists():
            languages.add("Python")
        if "React" in frameworks or "Next.js" in frameworks or "Vue" in frameworks:
            if not any(l in languages for l in ["TypeScript", "JavaScript"]):
                languages.add("JavaScript")

        return {
            "name": self.root_path.name,
            "languages": sorted(list(languages)),
            "frameworks": sorted(list(frameworks)),
            "package_managers": sorted(list(package_managers)),
            "databases": sorted(list(databases)),
            "routes_summary": routes_summary,
            "tests_summary": tests_summary,
            "has_docker": has_docker,
            "has_git": (self.root_path / ".git").exists(),
        }

    def _detect_languages(self) -> Set[str]:
        languages = set()
        extensions_map = {
            ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
            ".ts": "TypeScript", ".tsx": "TypeScript", ".php": "PHP",
            ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
            ".rb": "Ruby", ".c": "C", ".cpp": "C++", ".cs": "C#",
            ".html": "HTML", ".css": "CSS", ".vue": "Vue", ".sql": "SQL",
        }

        count = 0
        for p in self.root_path.rglob("*"):
            if count > 500:
                break
            if any(part.startswith(".") or part in ["node_modules", "vendor", "__pycache__", "venv", ".venv"] for part in p.parts):
                continue
            if p.is_file():
                count += 1
                ext = p.suffix.lower()
                if ext in extensions_map:
                    languages.add(extensions_map[ext])
        return languages

    def _detect_frameworks(self) -> Set[str]:
        frameworks = set()

        if (self.root_path / "artisan").exists() or (self.root_path / "composer.json").exists():
            composer_path = self.root_path / "composer.json"
            if composer_path.exists():
                try:
                    with open(composer_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        reqs = data.get("require", {})
                        if "laravel/framework" in reqs or (self.root_path / "artisan").exists():
                            frameworks.add("Laravel")
                        if "symfony/framework-bundle" in reqs:
                            frameworks.add("Symfony")
                except Exception:
                    if (self.root_path / "artisan").exists():
                        frameworks.add("Laravel")
            elif (self.root_path / "artisan").exists():
                frameworks.add("Laravel")

        package_json = self.root_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "next" in deps:
                        frameworks.add("Next.js")
                    if "react" in deps:
                        frameworks.add("React")
                    if "vue" in deps or "nuxt" in deps:
                        frameworks.add("Vue")
                    if "express" in deps:
                        frameworks.add("Express")
                    if "tailwindcss" in deps:
                        frameworks.add("Tailwind CSS")
            except Exception:
                pass

        if (self.root_path / "manage.py").exists():
            frameworks.add("Django")
        for py_file in self.root_path.glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if "fastapi" in content or "from fastapi import" in content:
                    frameworks.add("FastAPI")
                if "flask" in content or "from flask import" in content:
                    frameworks.add("Flask")
            except Exception:
                pass

        return frameworks

    def _detect_package_managers(self) -> Set[str]:
        managers = set()
        if (self.root_path / "composer.json").exists() or (self.root_path / "composer.lock").exists() or (self.root_path / "artisan").exists():
            managers.add("composer")
        if (self.root_path / "package.json").exists():
            managers.add("npm")
        if (self.root_path / "yarn.lock").exists():
            managers.add("yarn")
        if (self.root_path / "pnpm-lock.yaml").exists():
            managers.add("pnpm")
        if (self.root_path / "bun.lockb").exists() or (self.root_path / "bun.lock").exists():
            managers.add("bun")
        if (self.root_path / "pyproject.toml").exists() or (self.root_path / "requirements.txt").exists() or (self.root_path / "Pipfile").exists():
            managers.add("pip/poetry")
            managers.add("pip")
        if (self.root_path / "Cargo.toml").exists():
            managers.add("cargo")
        if (self.root_path / "go.mod").exists():
            managers.add("go modules")
        return managers

    def _detect_databases(self) -> Set[str]:
        databases = set()
        for p in self.root_path.rglob("*.sql"):
            databases.add("SQL")
            break
        if (self.root_path / "prisma").exists():
            databases.add("Prisma ORM")
        return databases

    def _detect_routes_structure(self) -> str:
        if (self.root_path / "routes").exists():
            return "routes/ directory found (Laravel/Express style)"
        if (self.root_path / "app" / "api").exists() or (self.root_path / "pages" / "api").exists():
            return "Next.js App/Pages API Router found"
        return "Standard file-based or decorator routing"

    def _detect_testing_framework(self) -> str:
        if (self.root_path / "phpunit.xml").exists() or (self.root_path / "phpunit.xml.dist").exists():
            return "PHPUnit"
        if (self.root_path / "pytest.ini").exists() or (self.root_path / "tests").exists():
            return "Pytest / Unittest"
        if (self.root_path / "jest.config.js").exists() or (self.root_path / "jest.config.ts").exists():
            return "Jest"
        return "Standard test suites"
