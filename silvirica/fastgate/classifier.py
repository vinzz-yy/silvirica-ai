from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
from silvirica.core.types import ComplexityLevel, RiskLevel


class FastGateClassifier:
    INSTANT_PATTERNS = [
        r"^where is\b", r"^find\s+(?:function|class|method|symbol|file|route|table)\b",
        r"^show\s+(?:file|route|diff|status|config|git)\b", r"^list\s+(?:routes|models|controllers|skills|memories)\b",
        r"^what is the (?:tech stack|framework|database)\b",
    ]
    SIMPLE_PATTERNS = [
        r"center\s+(?:this\s+)?button", r"fix\s+typo", r"rename\s+variable",
        r"format\s+code", r"add\s+comment", r"simple\s+css", r"change\s+color",
    ]
    COMPLEX_PATTERNS = [
        r"authentication", r"login", r"session", r"jwt", r"database\s+migration",
        r"race\s+condition", r"performance\s+bottleneck", r"refactor", r"payment\s+gateway",
    ]
    CRITICAL_PATTERNS = [
        r"multi-tenant", r"tenant\s+isolation", r"financial\s+record", r"security\s+vulnerability",
        r"sql\s+injection", r"remote\s+code\s+execution", r"privilege\s+escalation",
        r"production\s+deployment", r"delete\s+(?:all|database|table)",
    ]
    SKILL_TRIGGERS = {
        "security-audit": ["security", "vulnerability", "auth", "permission", "jwt", "csrf", "xss", "idor", "tenant", "secret", "password"],
        "debugging": ["bug", "error", "exception", "failed", "crash", "traceback", "fix", "issue", "why does", "why can"],
        "ui-ux-pro": ["button", "css", "layout", "color", "font", "responsive", "mobile", "modal", "accessibility", "wcag", "tailwind", "ui", "ux", "center"],
        "database": ["database", "sql", "migration", "query", "schema", "table", "prisma", "eloquent", "postgres", "mysql"],
        "performance": ["slow", "optimize", "latency", "bottleneck", "cache", "memory leak", "profiling", "n+1"],
        "testing": ["test", "phpunit", "pytest", "jest", "coverage", "mock", "assert", "tdd"],
        "architecture": ["architecture", "adr", "design pattern", "structure", "module", "refactor", "system", "conventions"],
        "git": ["git", "commit", "branch", "diff", "merge", "conflict", "rebase"],
    }

    @classmethod
    def classify(cls, query: str) -> Dict[str, Any]:
        query_clean = query.strip()
        query_lower = query_clean.lower()

        intent = "general_coding"
        complexity = ComplexityLevel.LEVEL_2_STANDARD
        risk = RiskLevel.SAFE
        reasoning_budget = 2500

        for pat in cls.INSTANT_PATTERNS:
            if re.search(pat, query_lower):
                matched_skills = cls._match_skills(query_lower)
                return {
                    "intent": "lookup",
                    "complexity": ComplexityLevel.LEVEL_0_INSTANT,
                    "risk": RiskLevel.SAFE,
                    "skills": matched_skills,
                    "reasoning_budget": 200,
                }

        for pat in cls.CRITICAL_PATTERNS:
            if re.search(pat, query_lower):
                matched_skills = cls._match_skills(query_lower)
                if "security-audit" not in matched_skills:
                    matched_skills.append("security-audit")
                return {
                    "intent": "critical_security_analysis",
                    "complexity": ComplexityLevel.LEVEL_5_CRITICAL,
                    "risk": RiskLevel.CRITICAL,
                    "skills": matched_skills,
                    "reasoning_budget": 12000,
                }

        for pat in cls.SIMPLE_PATTERNS:
            if re.search(pat, query_lower):
                matched_skills = cls._match_skills(query_lower)
                return {
                    "intent": "quick_edit",
                    "complexity": ComplexityLevel.LEVEL_0_INSTANT if "center" in query_lower else ComplexityLevel.LEVEL_1_SIMPLE,
                    "risk": RiskLevel.SAFE,
                    "skills": matched_skills,
                    "reasoning_budget": 800,
                }

        for pat in cls.COMPLEX_PATTERNS:
            if re.search(pat, query_lower):
                matched_skills = cls._match_skills(query_lower)
                return {
                    "intent": "complex_task",
                    "complexity": ComplexityLevel.LEVEL_3_COMPLEX,
                    "risk": RiskLevel.MEDIUM,
                    "skills": matched_skills,
                    "reasoning_budget": 6000,
                }

        matched_skills = cls._match_skills(query_lower)
        return {
            "intent": intent,
            "complexity": complexity,
            "risk": risk,
            "skills": matched_skills,
            "reasoning_budget": reasoning_budget,
        }

    @classmethod
    def _match_skills(cls, query_lower: str) -> List[str]:
        matched = []
        for skill_name, triggers in cls.SKILL_TRIGGERS.items():
            if any(t in query_lower for t in triggers):
                matched.append(skill_name)
        if not matched:
            matched.append("coding-core")
        return matched


# Compatibility alias
TaskClassifier = FastGateClassifier
