from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple

from silvirica.capabilities.jev.adapter import JevAdapter
from silvirica.capabilities.jev.fallback import NativeFallbackRouter
from silvirica.capabilities.jev.schemas import (
    JevComplexity,
    JevDecision,
    JevExecutionPath,
    JevModelTier,
)


class JevTaskClassifier:
    """
    High-speed Task Classifier & Complexity Assessor.
    Classifies tasks into Simple, Medium, or Advanced, while isolating fast-path zero-LLM tasks.
    """

    def __init__(self, adapter: Optional[JevAdapter] = None):
        self.adapter = adapter or JevAdapter()

    def is_deterministic_fast_path(self, task: str) -> Tuple[bool, Optional[str]]:
        """
        Determines if the task can be answered with zero LLM calls
        (e.g., symbol lookup, file locating, exact keyword search).
        """
        t = task.strip().lower()
        if re.match(r"^(locate|find|where is|get path for)\s+(file|symbol|class|function|def)\s+[\w\.\-]+$", t):
            return True, "deterministic_symbol_or_file_lookup"
        if re.match(r"^(show|view|cat|read)\s+file\s+[\w\.\/\\]+$", t):
            return True, "deterministic_file_read"
        return False, None

    def classify(
        self,
        task: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
    ) -> JevDecision:
        """
        Classifies task complexity and returns a structured JevDecision.
        """
        # 1. Check if purely deterministic fast path (0 tokens, instant)
        is_fast, fast_reason = self.is_deterministic_fast_path(task)
        if is_fast:
            return JevDecision(
                complexity=JevComplexity.SIMPLE,
                confidence=1.0,
                route="instant_fast_path",
                skills=["coding-core"],
                context_budget=500,
                model_tier=JevModelTier.FAST,
                deep_reasoning=False,
                needs_escalation=False,
                execution_path=JevExecutionPath.FAST_PATH,
                latency_ms=0.1,
                source="deterministic_classifier",
                reasons=fast_reason,
            )

        # 2. Invoke JevAdapter with fallback safety
        try:
            return self.adapter.decide(
                task_query=task,
                project_context=project_context,
                available_skills=available_skills,
            )
        except Exception as e:
            return NativeFallbackRouter.evaluate(
                task=task,
                project_context=project_context,
                available_skills=available_skills,
                reason=f"JEV classifier fallback due to: {str(e)}",
            )
