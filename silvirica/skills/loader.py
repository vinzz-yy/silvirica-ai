from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from silvirica.skills.registry import SkillDefinition

BUILTIN_SKILLS: Dict[str, SkillDefinition] = {
    "coding-core": SkillDefinition(
        name="coding-core", version="1.0.0",
        description="Clean coding, syntactic correctness, and minimal diff discipline.",
        triggers=["code", "implement", "function", "class", "refactor"], priority="high",
        summary="Write minimal, robust, idiomatic code.",
        instructions="1. Read symbol signatures.\n2. Make surgical edits.\n3. Maintain strict type safety.",
        tools=["symbol_index", "ast_search", "git_diff"], knowledge=["SOLID", "Clean Code"],
    ),
    "debugging": SkillDefinition(
        name="debugging", version="1.0.0",
        description="Root-cause debugging and error traceback analysis.",
        triggers=["bug", "error", "exception", "failed", "crash", "fix", "issue", "why does", "why can"],
        priority="high", summary="Isolate failure root causes, check failure memory.",
        instructions="1. Retrieve past failure memory.\n2. Inspect stack trace.\n3. Verify fix.",
        tools=["failure_memory", "symbol_index", "test_runner"], knowledge=["Root Cause Analysis", "Fault Localization"],
    ),
    "security-audit": SkillDefinition(
        name="security-audit", version="1.0.0",
        description="Defensive security analysis and credential protection.",
        triggers=["security", "vulnerability", "auth", "permission", "jwt", "csrf", "xss", "idor", "tenant", "injection"],
        priority="critical", summary="Detect OWASP vulnerabilities.",
        instructions="1. Scan input boundaries.\n2. Audit authorization logic.\n3. Ensure secrets are redacted against OWASP Top 10.",
        tools=["security_scanner", "secret_scanner"], knowledge=["OWASP Top 10", "CWE"],
    ),
    "ui-ux-pro": SkillDefinition(
        name="ui-ux-pro", version="1.0.0",
        description="Production UI/UX, design systems, accessibility (WCAG).",
        triggers=["button", "css", "layout", "color", "font", "responsive", "mobile", "modal", "accessibility", "wcag", "tailwind", "ui", "ux", "center"],
        priority="medium", summary="Engineer responsive, accessible, consistent UI.",
        instructions="1. Check design tokens.\n2. Ensure WCAG 2.1 AA accessibility.",
        tools=["design_system_analyzer", "css_inspector"], knowledge=["WCAG 2.1", "Responsive Design"],
    ),
    "database": SkillDefinition(
        name="database", version="1.0.0",
        description="Database schema, query optimization, indexing.",
        triggers=["database", "sql", "migration", "query", "schema", "table", "prisma", "eloquent", "postgres", "mysql"],
        priority="high", summary="Optimize relational queries and guard migrations.",
        instructions="1. Block automatic destructive alterations.\n2. Index frequently queried columns.",
        tools=["schema_inspector", "query_analyzer"], knowledge=["SQL Indexing", "Query Plans"],
    ),
    "architecture": SkillDefinition(
        name="architecture", version="1.0.0",
        description="System architecture, modularity, ADR recording.",
        triggers=["architecture", "adr", "design pattern", "structure", "module", "system", "conventions"],
        priority="high", summary="Maintain modular boundaries and record ADRs.",
        instructions="1. Inspect graph dependencies.\n2. Record decisions in memory.",
        tools=["graph_engine", "decision_memory"], knowledge=["Hexagonal Architecture", "Clean Architecture"],
    ),
    "performance": SkillDefinition(
        name="performance", version="1.0.0",
        description="Latency reduction, token optimization, cache strategy.",
        triggers=["slow", "optimize", "latency", "bottleneck", "cache", "memory leak", "profiling", "n+1"],
        priority="medium", summary="Profile hot paths and maximize cache efficiency.",
        instructions="1. Measure before optimizing.\n2. Implement caching.",
        tools=["telemetry_store", "profiler"], knowledge=["Time/Space Complexity"],
    ),
    "testing": SkillDefinition(
        name="testing", version="1.0.0",
        description="Test suite construction and hostile scenario validation.",
        triggers=["test", "phpunit", "pytest", "jest", "coverage", "mock", "assert", "tdd"],
        priority="medium", summary="Build reliable unit and integration tests.",
        instructions="1. Test happy paths and failure modes.\n2. Avoid brittle mocks.",
        tools=["test_runner"], knowledge=["TDD", "Unit Testing"],
    ),
    "git": SkillDefinition(
        name="git", version="1.0.0",
        description="Git change tracking and atomic commits.",
        triggers=["git", "commit", "branch", "diff", "merge", "conflict", "rebase"],
        priority="low", summary="Track diffs and produce clean atomic commits.",
        instructions="1. Inspect diffs before committing.\n2. Never commit secrets.",
        tools=["git_watcher"], knowledge=["Conventional Commits"],
    ),
    "research": SkillDefinition(
        name="research", version="1.0.0",
        description="Deep codebase and documentation grounding.",
        triggers=["research", "investigate", "explore", "compare", "study"],
        priority="medium", summary="Ground technical decisions in repository evidence.",
        instructions="1. Gather references.\n2. Check verified project memory.",
        tools=["graph_search", "memory_vault"], knowledge=["Evidence Grounding"],
    ),
    "planning": SkillDefinition(
        name="planning", version="1.0.0",
        description="Structured task planning and verification gates.",
        triggers=["plan", "roadmap", "breakdown", "milestones", "scope"],
        priority="high", summary="Break complex features into verifiable tasks.",
        instructions="1. Define affected files.\n2. State explicit verification criteria.",
        tools=["impact_analyzer", "graph_db"], knowledge=["Structured Task Breakdown"],
    ),
}


class SkillLoader:
    def __init__(self, custom_skills_dir: Optional[Path] = None):
        self.custom_skills_dir = custom_skills_dir
        self.skills: Dict[str, SkillDefinition] = dict(BUILTIN_SKILLS)
        self._load_all_skill_sources()

    def _load_all_skill_sources(self) -> None:
        # 1. Custom skills dir
        if self.custom_skills_dir and self.custom_skills_dir.exists():
            self._scan_skill_directory(self.custom_skills_dir)

        # 2. Workspace root skills dir
        root_skills = Path(__file__).resolve().parent.parent.parent / "skills"
        if root_skills.exists():
            self._scan_skill_directory(root_skills)

    def _scan_skill_directory(self, base_dir: Path) -> None:
        try:
            for item in base_dir.iterdir():
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    if skill_md.exists():
                        self._parse_skill_md(skill_md, item.name)
                elif item.is_file() and item.suffix in [".yaml", ".yml"]:
                    self._parse_skill_yaml(item)
        except Exception:
            pass

    def _parse_skill_yaml(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "name" in data:
                    self.skills[data["name"]] = SkillDefinition(
                        name=data["name"],
                        version=str(data.get("version", "1.0.0")),
                        description=data.get("description", ""),
                        triggers=data.get("triggers", []),
                        priority=data.get("priority", "medium"),
                        summary=data.get("summary", ""),
                        instructions=data.get("instructions", ""),
                        tools=data.get("tools", []),
                        knowledge=data.get("knowledge", []),
                    )
        except Exception:
            pass

    def _parse_skill_md(self, path: Path, folder_name: str) -> None:
        try:
            raw = path.read_text(encoding="utf-8-sig", errors="ignore").strip()
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    name = str(fm.get("name", folder_name)).strip('"\'')
                    desc = str(fm.get("description", ""))
                    triggers = [folder_name, name]
                    if "triggers" in fm and isinstance(fm["triggers"], list):
                        triggers.extend(fm["triggers"])
                    elif "use when the user says:" in desc.lower():
                        clause = desc.lower().split("use when the user says:")[-1]
                        triggers.extend([t.strip().rstrip(".").strip('"\'') for t in clause.split(",") if t.strip()])

                    summary = desc[:200] if desc else f"Specialized skill for {name}."
                    self.skills[name] = SkillDefinition(
                        name=name,
                        version="1.0.0",
                        description=desc,
                        triggers=list(set(triggers)),
                        priority="medium",
                        summary=summary,
                        instructions=body[:3000],
                        tools=["symbol_index", "context_compiler"],
                        knowledge=[],
                    )
            else:
                # If no YAML frontmatter, treat folder name as skill name
                self.skills[folder_name] = SkillDefinition(
                    name=folder_name,
                    version="1.0.0",
                    description=raw[:200],
                    triggers=[folder_name],
                    priority="medium",
                    summary=raw[:200],
                    instructions=raw[:3000],
                    tools=["symbol_index", "context_compiler"],
                    knowledge=[],
                )
        except Exception:
            pass

    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        return self.skills.get(name)

    def load_skill(self, name: str) -> Optional[SkillDefinition]:
        return self.get_skill(name)

    def list_skills(self) -> List[SkillDefinition]:
        return list(self.skills.values())

    def list_available_skills(self) -> List[SkillDefinition]:
        return self.list_skills()

    def match_skills(self, query: str) -> List[str]:
        query_lower = query.lower()
        matched = []
        for name, skill in self.skills.items():
            if any(t in query_lower for t in skill.triggers):
                matched.append(name)
        if not matched:
            matched.append("coding-core")
        return matched

    def load_skills_level1(self, skill_names: List[str]) -> str:
        summaries = []
        for name in skill_names:
            skill = self.get_skill(name)
            if skill:
                summaries.append(f"### Skill: {skill.name}\n{skill.summary}")
        return "\n\n".join(summaries)

    def load_skills_level2(self, skill_names: List[str]) -> str:
        instructions = []
        for name in skill_names:
            skill = self.get_skill(name)
            if skill:
                instructions.append(f"### Skill: {skill.name}\n{skill.instructions}\nTools: {', '.join(skill.tools)}")
        return "\n\n".join(instructions)
