from __future__ import annotations
from dataclasses import dataclass
from typing import List
from silvirica.core.types import ComplexityLevel


@dataclass
class BenchmarkScenario:
    id: str
    title: str
    task: str
    expected_complexity: ComplexityLevel
    target_files: List[str]
    naive_estimated_tokens: int
    is_zero_model_expected: bool = False


BENCHMARK_SCENARIOS: List[BenchmarkScenario] = [
    BenchmarkScenario(
        id="SCENARIO-01-ZERO-MODEL",
        title="Symbol Lookup (Where is AuthController?)",
        task="Where is AuthController defined in the codebase?",
        expected_complexity=ComplexityLevel.LEVEL_0_INSTANT,
        target_files=["silvirica/core/project.py"],
        naive_estimated_tokens=8500,
        is_zero_model_expected=True,
    ),
    BenchmarkScenario(
        id="SCENARIO-02-TRIVIAL-UI",
        title="Trivial UI CSS Centering",
        task="Center this login button with CSS flexbox",
        expected_complexity=ComplexityLevel.LEVEL_0_INSTANT,
        target_files=["silvirica/uiux/design_system.py"],
        naive_estimated_tokens=12000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-03-AUTH-DEBUG",
        title="Authentication Middleware Loop",
        task="Find why users cannot log in due to session middleware redirect",
        expected_complexity=ComplexityLevel.LEVEL_2_STANDARD,
        target_files=["silvirica/core/types.py", "silvirica/context/compiler.py"],
        naive_estimated_tokens=32000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-04-SECURITY-AUDIT",
        title="Tenant Isolation Security Verification",
        task="Determine whether tenants can access each other's financial records via IDOR or missing authorization check",
        expected_complexity=ComplexityLevel.LEVEL_5_CRITICAL,
        target_files=["silvirica/security/engine.py", "silvirica/security/rules.py"],
        naive_estimated_tokens=54000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-05-ARCHITECTURE-ADR",
        title="Architecture Decision Memory Lookup",
        task="Show architectural decisions and conventions regarding database migrations and ORM usage",
        expected_complexity=ComplexityLevel.LEVEL_2_STANDARD,
        target_files=["silvirica/memory/decision_memory.py", "silvirica/memory/vault.py"],
        naive_estimated_tokens=22000,
        is_zero_model_expected=False,
    ),
]
