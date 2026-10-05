from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from silvirica.capabilities.jev.schemas import (
    JevComplexity,
    JevDecision,
    JevExecutionPath,
    JevModelTier,
)
from silvirica.core.types import ComplexityLevel, RoutingCategory


class NativeFallbackRouter:
    """
    Zero-downtime native router fallback for JEV.
    When JEV is unconfigured, disabled, timed out, or circuit-tripped, this fallback
    executes Silvirica's native rule-based decision logic in < 2ms.
    """

    @classmethod
    def evaluate(
        cls,
        task: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
        reason: Optional[str] = None,
    ) -> JevDecision:
        start_time = time.time()
        t = task.lower().strip()

        # Skill selection heuristics
        selected_skills = []
        all_skills = available_skills or [
            "coding-core", "debugging", "security-and-hardening",
            "frontend-ui-engineering", "performance-optimization",
            "test-driven-development", "planning-and-task-breakdown"
        ]

        # Native rule classification
        is_security = any(k in t for k in ["vulnerab", "cve", "injection", "xss", "csrf", "ssrf", "auth", "secret", "crypto"])
        is_architect = any(k in t for k in ["architect", "redesign", "refactor system", "concurrency", "distributed"])
        is_debug = any(k in t for k in ["error", "bug", "exception", "traceback", "fix", "fail", "crash"])
        is_test = any(k in t for k in ["test", "tdd", "pytest", "unit test", "mock"])
        is_perf = any(k in t for k in ["slow", "latency", "optimize", "bottleneck", "memory leak"])
        is_ui = any(k in t for k in ["ui", "css", "html", "react", "frontend", "styling", "component"])
        is_simple = any(t.startswith(p) for p in ["explain", "what is", "locate", "where is", "find", "rename", "format"])

        if is_security and "security-and-hardening" in all_skills:
            selected_skills.append("security-and-hardening")
        if is_debug and "debugging" in all_skills:
            selected_skills.append("debugging")
        if is_test and "test-driven-development" in all_skills:
            selected_skills.append("test-driven-development")
        if is_perf and "performance-optimization" in all_skills:
            selected_skills.append("performance-optimization")
        if is_ui and "frontend-ui-engineering" in all_skills:
            selected_skills.append("frontend-ui-engineering")
        if is_architect and "planning-and-task-breakdown" in all_skills:
            selected_skills.append("planning-and-task-breakdown")

        if not selected_skills:
            selected_skills = ["coding-core"]

        if is_security or is_architect:
            complexity = JevComplexity.ADVANCED
            model_tier = JevModelTier.REASONING if is_security else JevModelTier.POWERFUL
            route = "security" if is_security else "architect"
            context_budget = 12000
            deep_reasoning = True
            execution_path = JevExecutionPath.DEEP_PATH
        elif is_debug or is_test or is_perf or is_ui or len(t.split()) > 25:
            complexity = JevComplexity.MEDIUM
            model_tier = JevModelTier.STANDARD
            route = "debug" if is_debug else "feature"
            context_budget = 6000
            deep_reasoning = False
            execution_path = JevExecutionPath.STANDARD_PATH
        else:
            complexity = JevComplexity.SIMPLE
            model_tier = JevModelTier.FAST
            route = "fast"
            context_budget = 2000
            deep_reasoning = False
            execution_path = JevExecutionPath.FAST_PATH

        latency_ms = (time.time() - start_time) * 1000.0

        return JevDecision(
            complexity=complexity,
            confidence=0.85,
            route=route,
            skills=selected_skills,
            context_budget=context_budget,
            model_tier=model_tier,
            deep_reasoning=deep_reasoning,
            needs_escalation=False,
            execution_path=execution_path,
            latency_ms=latency_ms,
            source="native_fallback",
            reasons=reason or "Executed native Silvirica router",
        )
