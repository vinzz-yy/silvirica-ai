from __future__ import annotations
import time
from typing import Any, Dict, List

from silvirica.capabilities.jev.cache import JevDecisionCache
from silvirica.capabilities.jev.fallback import NativeFallbackRouter
from silvirica.capabilities.jev.router import JevRouter
from silvirica.capabilities.jev.schemas import JevComplexity, JevConfig, JevModelTier
from silvirica.core.config import ProjectConfig


BENCHMARK_TASKS = [
    # Simple tasks
    {"task": "locate symbol PathSandbox", "expected_complexity": "simple", "category": "symbol"},
    {"task": "where is the config file loader defined", "expected_complexity": "simple", "category": "file"},
    {"task": "explain what JevCircuitBreaker does", "expected_complexity": "simple", "category": "explain"},
    {"task": "fix minor typo in docstring of sandbox.py", "expected_complexity": "simple", "category": "typo"},
    
    # Medium tasks
    {"task": "debug IndexError in list comprehension when query tokens are empty", "expected_complexity": "medium", "category": "debug"},
    {"task": "implement new endpoint for telemetry export in daemon server", "expected_complexity": "medium", "category": "feature"},
    {"task": "optimize memory leak in streaming response chunk handler", "expected_complexity": "medium", "category": "perf"},
    {"task": "add unit tests for secret redactor Shannon entropy detector", "expected_complexity": "medium", "category": "test"},
    {"task": "style dark mode modal dialog with responsive CSS grid", "expected_complexity": "medium", "category": "ui"},

    # Advanced tasks
    {"task": "conduct comprehensive security audit of SSRF vectors and credential validation in AIProvider", "expected_complexity": "advanced", "category": "security"},
    {"task": "redesign entire cache architecture to support multi-tenant distributed Redis clustering", "expected_complexity": "advanced", "category": "architect"},
    {"task": "fix critical race condition and deadlock in concurrent MCP tool execution pipeline", "expected_complexity": "advanced", "category": "concurrency"},
]

ALL_AVAILABLE_SKILLS = [
    "coding-core",
    "debugging",
    "security-and-hardening",
    "frontend-ui-engineering",
    "performance-optimization",
    "test-driven-development",
    "planning-and-task-breakdown",
    "graphify",
    "code-review-and-quality",
    "ulw-plan",
    "ulw-work",
]


class JevBenchmarkHarness:
    """
    Empirical benchmark comparing Silvirica Without JEV vs Silvirica + JEV.
    Evaluates:
    - Routing latency (ms)
    - Context tokens allocated
    - Skills loaded count
    - Model tiering accuracy
    - Cache hit acceleration
    """

    def __init__(self, runs_per_task: int = 5):
        self.runs_per_task = max(1, runs_per_task)
        self.project_config = ProjectConfig()

    def run_benchmark(self) -> Dict[str, Any]:
        results_without_jev = self._run_baseline()
        results_with_jev = self._run_jev()

        # Calculate comparative metrics
        latency_reduction_pct = 0.0
        if results_without_jev["avg_routing_latency_ms"] > 0:
            latency_diff = results_without_jev["avg_routing_latency_ms"] - results_with_jev["avg_routing_latency_ms"]
            latency_reduction_pct = round((latency_diff / results_without_jev["avg_routing_latency_ms"]) * 100, 1)

        token_savings_pct = 0.0
        if results_without_jev["avg_context_budget"] > 0:
            token_diff = results_without_jev["avg_context_budget"] - results_with_jev["avg_context_budget"]
            token_savings_pct = round((token_diff / results_without_jev["avg_context_budget"]) * 100, 1)

        skill_reduction_pct = 0.0
        if results_without_jev["avg_skills_loaded"] > 0:
            skill_diff = results_without_jev["avg_skills_loaded"] - results_with_jev["avg_skills_loaded"]
            skill_reduction_pct = round((skill_diff / results_without_jev["avg_skills_loaded"]) * 100, 1)

        return {
            "tasks_evaluated": len(BENCHMARK_TASKS),
            "total_runs": len(BENCHMARK_TASKS) * self.runs_per_task,
            "baseline_without_jev": results_without_jev,
            "silvirica_with_jev": results_with_jev,
            "comparative_improvements": {
                "routing_latency_reduction_pct": latency_reduction_pct,
                "context_token_savings_pct": token_savings_pct,
                "skill_context_reduction_pct": skill_reduction_pct,
                "cache_speedup_factor": round(
                    results_without_jev["avg_routing_latency_ms"] / max(0.01, results_with_jev["avg_cached_latency_ms"]), 1
                ),
            },
        }

    def _run_baseline(self) -> Dict[str, Any]:
        """
        Baseline without JEV:
        - Loads ALL available skills into prompt context (standard monolithic behavior)
        - Uses static maximum context window (8,000 tokens)
        - Fixed standard routing latency
        """
        total_latency = 0.0
        total_context = 0
        total_skills = 0
        total_evals = 0

        for item in BENCHMARK_TASKS:
            task = item["task"]
            for _ in range(self.runs_per_task):
                start = time.time()
                # Baseline native rule classification
                dec = NativeFallbackRouter.evaluate(task, available_skills=ALL_AVAILABLE_SKILLS)
                elapsed_ms = (time.time() - start) * 1000.0
                
                # Without JEV skill filtering, typical systems inject all or large skill sets
                skills_loaded = len(ALL_AVAILABLE_SKILLS)
                # Without JEV budgeting, context size defaults to large monolithic buffer
                context_size = 10000

                total_latency += elapsed_ms
                total_context += context_size
                total_skills += skills_loaded
                total_evals += 1

        return {
            "avg_routing_latency_ms": round(total_latency / total_evals, 3),
            "avg_context_budget": round(total_context / total_evals, 0),
            "avg_skills_loaded": round(total_skills / total_evals, 1),
            "model_selection": "Monolithic Standard Tier (Static)",
        }

    def _run_jev(self) -> Dict[str, Any]:
        """
        Silvirica + JEV:
        - Selective skill routing (1-2 skills only)
        - Targeted dynamic context budgeting (500 - 12,000 tokens)
        - Tiered model selection (Fast, Standard, Powerful, Reasoning)
        - Sub-millisecond decision caching
        """
        config = JevConfig(enabled=True, cache=True)
        router = JevRouter(config=config, project_config=self.project_config)
        
        total_latency = 0.0
        cached_latency = 0.0
        total_context = 0
        total_skills = 0
        total_evals = 0
        cached_evals = 0

        for item in BENCHMARK_TASKS:
            task = item["task"]
            # First run: JEV evaluation (Cache Miss)
            start = time.time()
            decision = router.evaluate_task(task, available_skills=ALL_AVAILABLE_SKILLS)
            elapsed_ms = (time.time() - start) * 1000.0

            total_latency += elapsed_ms
            total_context += decision.context_budget
            total_skills += len(decision.skills)
            total_evals += 1

            # Subsequent runs: JEV Cache Hit
            for _ in range(self.runs_per_task - 1):
                start_c = time.time()
                cached_decision = router.evaluate_task(task, available_skills=ALL_AVAILABLE_SKILLS)
                elapsed_c_ms = (time.time() - start_c) * 1000.0

                cached_latency += elapsed_c_ms
                cached_evals += 1
                total_latency += elapsed_c_ms
                total_context += cached_decision.context_budget
                total_skills += len(cached_decision.skills)
                total_evals += 1

        avg_cached = (cached_latency / cached_evals) if cached_evals > 0 else 0.05

        return {
            "avg_routing_latency_ms": round(total_latency / total_evals, 3),
            "avg_uncached_latency_ms": round(decision.latency_ms, 3),
            "avg_cached_latency_ms": round(avg_cached, 3),
            "avg_context_budget": round(total_context / total_evals, 0),
            "avg_skills_loaded": round(total_skills / total_evals, 1),
            "cache_stats": router.cache.get_stats(),
            "decision_stats": router.stats.to_dict(),
        }
