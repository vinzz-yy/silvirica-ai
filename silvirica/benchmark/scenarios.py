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
        id="SCENARIO-01-SYMBOL-LOOKUP",
        title="Symbol Lookup (Where is AuthController?)",
        task="Where is AuthController defined in the codebase?",
        expected_complexity=ComplexityLevel.LEVEL_0_INSTANT,
        target_files=["silvirica/core/project.py"],
        naive_estimated_tokens=18500,
        is_zero_model_expected=True,
    ),
    BenchmarkScenario(
        id="SCENARIO-02-FILE-LOOKUP",
        title="File Path Discovery",
        task="Where is file config.yaml?",
        expected_complexity=ComplexityLevel.LEVEL_0_INSTANT,
        target_files=["silvirica/core/config.py"],
        naive_estimated_tokens=14000,
        is_zero_model_expected=True,
    ),
    BenchmarkScenario(
        id="SCENARIO-03-BUG-FIXING",
        title="Bug Investigation (Login Loop)",
        task="Why did login break after recent authentication middleware change?",
        expected_complexity=ComplexityLevel.LEVEL_2_STANDARD,
        target_files=["silvirica/core/types.py", "silvirica/context/compiler.py"],
        naive_estimated_tokens=34000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-04-FEATURE-IMPL",
        title="Feature Implementation (Rate Limiter)",
        task="Implement token bucket rate limiter middleware for API routes",
        expected_complexity=ComplexityLevel.LEVEL_3_COMPLEX,
        target_files=["silvirica/core/types.py", "silvirica/context/compiler.py"],
        naive_estimated_tokens=42000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-05-LARGE-REPO-DEBUG",
        title="Large-Repository Dependency Debugging",
        task="Trace multi-hop call graph from UserService to DatabasePool and check for deadlock",
        expected_complexity=ComplexityLevel.LEVEL_4_DEEP,
        target_files=["silvirica/graph/graph_db.py", "silvirica/graph/impact.py"],
        naive_estimated_tokens=68000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-06-SECURITY-REVIEW",
        title="Defensive Security & IDOR Review",
        task="Audit tenant isolation boundaries and financial record access for IDOR vulnerabilities",
        expected_complexity=ComplexityLevel.LEVEL_5_CRITICAL,
        target_files=["silvirica/security/engine.py", "silvirica/security/rules.py"],
        naive_estimated_tokens=56000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-07-ARCHITECTURE-ANALYSIS",
        title="Architecture Decision Memory Analysis",
        task="Show architectural decisions and conventions regarding database migrations and ORM usage",
        expected_complexity=ComplexityLevel.LEVEL_2_STANDARD,
        target_files=["silvirica/memory/decision_memory.py", "silvirica/memory/vault.py"],
        naive_estimated_tokens=28000,
        is_zero_model_expected=False,
    ),
    BenchmarkScenario(
        id="SCENARIO-08-REFACTORING",
        title="Codebase Modular Refactoring",
        task="Refactor monolithic controller into modular service handlers following clean architecture",
        expected_complexity=ComplexityLevel.LEVEL_3_COMPLEX,
        target_files=["silvirica/repository/ast_parser.py", "silvirica/repository/indexer.py"],
        naive_estimated_tokens=48000,
        is_zero_model_expected=False,
    ),
]
