from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from silvirica.capabilities.jev.adapter import JevAdapter
from silvirica.capabilities.jev.cache import JevDecisionCache
from silvirica.capabilities.jev.classifier import JevTaskClassifier
from silvirica.capabilities.jev.fallback import NativeFallbackRouter
from silvirica.capabilities.jev.schemas import (
    JevComplexity,
    JevConfig,
    JevDecision,
    JevExecutionPath,
    JevModelTier,
    JevStats,
)
from silvirica.context.redactor import SecretRedactor, SecurityMode


class JevRouter:
    """
    Core JEV Decision Intelligence & Routing Engine.
    Coordinates cache, deterministic fast-path, JEV System One intelligence,
    circuit breaker, and native fallback.
    """

    def __init__(
        self,
        config: Optional[JevConfig] = None,
        project_config: Optional[Any] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.config = config or JevConfig()
        self.project_config = project_config
        self.cache_dir = cache_dir or (Path.cwd() / ".silvirica" / "cache")
        self.cache = JevDecisionCache(cache_dir=self.cache_dir)
        self.adapter = JevAdapter(config=self.config)
        self.classifier = JevTaskClassifier(adapter=self.adapter)
        self.stats = JevStats()

    def evaluate_task(
        self,
        task: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
        state_hash: str = "",
        bypass_cache: bool = False,
    ) -> JevDecision:
        """
        Full decision pipeline:
        1. Pre-Redaction
        2. Fast Deterministic Gate
        3. Cache Lookup
        4. JEV Decision
        5. Fallback on Error / Timeout / Circuit Trip
        """
        start_time = time.time()
        self.stats.total_decisions += 1

        # Pre-redact task string
        safe_task = SecretRedactor.sanitize_text(task, mode=SecurityMode.ACTIVE_REDACTION)

        # 1. Deterministic Fast Gate (< 0.1 ms, 0 tokens)
        is_fast, fast_reason = self.classifier.is_deterministic_fast_path(safe_task)
        if is_fast:
            decision = JevDecision(
                complexity=JevComplexity.SIMPLE,
                confidence=1.0,
                route="instant_fast_path",
                skills=["coding-core"],
                context_budget=500,
                model_tier=JevModelTier.FAST,
                deep_reasoning=False,
                needs_escalation=False,
                execution_path=JevExecutionPath.FAST_PATH,
                latency_ms=(time.time() - start_time) * 1000.0,
                source="fast_gate",
                reasons=fast_reason,
            )
            self._update_stats_for_decision(decision)
            return decision

        # 2. Decision Cache (< 1 ms, 0 tokens)
        cache_key = ""
        if self.config.cache and not bypass_cache:
            proj_name = getattr(self.project_config, "name", "") if self.project_config else ""
            cache_key = self.cache.generate_fingerprint(
                task=safe_task,
                project_name=proj_name,
                state_hash=state_hash,
            )
            cached = self.cache.get(cache_key, state_hash=state_hash)
            if cached:
                cached.latency_ms = (time.time() - start_time) * 1000.0
                self.stats.cache_hits += 1
                self._update_stats_for_decision(cached)
                return cached

        # 3. JEV Decision Layer (Target < 500 ms)
        if self.config.enabled and self.adapter.is_available():
            try:
                self.stats.jev_calls += 1
                decision = self.adapter.decide(
                    task_query=safe_task,
                    project_context=project_context,
                    available_skills=available_skills,
                )
                decision.latency_ms = (time.time() - start_time) * 1000.0

                # Cache successful decision
                if self.config.cache and cache_key:
                    self.cache.set(cache_key, decision, state_hash=state_hash)

                self._update_stats_for_decision(decision)
                return decision
            except Exception as e:
                # Immediate fallback
                self.stats.native_fallbacks += 1
                fallback_decision = NativeFallbackRouter.evaluate(
                    task=safe_task,
                    project_context=project_context,
                    available_skills=available_skills,
                    reason=f"Fallback from JEV: {str(e)}",
                )
                fallback_decision.latency_ms = (time.time() - start_time) * 1000.0
                self._update_stats_for_decision(fallback_decision)
                return fallback_decision
        else:
            # JEV disabled or circuit open -> Native Fallback immediately (< 2 ms)
            self.stats.native_fallbacks += 1
            if not self.adapter.is_available() and self.config.enabled:
                self.stats.circuit_trips += 1
            fallback_decision = NativeFallbackRouter.evaluate(
                task=safe_task,
                project_context=project_context,
                available_skills=available_skills,
                reason="JEV disabled or circuit breaker open",
            )
            fallback_decision.latency_ms = (time.time() - start_time) * 1000.0
            self._update_stats_for_decision(fallback_decision)
            return fallback_decision

    def select_model(self, decision: JevDecision) -> str:
        """
        Maps JevModelTier to configured provider model strings.
        """
        if self.project_config and hasattr(self.project_config, "routing"):
            routing = self.project_config.routing
            tier = decision.model_tier
            if tier == JevModelTier.FAST:
                return getattr(routing, "quick_model", "gpt-4o-mini") or getattr(routing, "instant_model", "local-deterministic")
            elif tier == JevModelTier.STANDARD:
                return getattr(routing, "standard_model", "gpt-4o-mini") or getattr(routing, "coder_model", "gpt-4o")
            elif tier == JevModelTier.POWERFUL:
                return getattr(routing, "deep_model", "o3-mini") or getattr(routing, "architect_model", "o3-mini")
            elif tier == JevModelTier.REASONING:
                return getattr(routing, "security_model", "gpt-4o") or getattr(routing, "ultrabrain_model", "o1")
            return getattr(routing, "standard_model", "gpt-4o-mini")

        tier = decision.model_tier
        if tier == JevModelTier.FAST:
            return "gpt-4o-mini"
        elif tier == JevModelTier.STANDARD:
            return "gpt-4o-mini"
        elif tier == JevModelTier.POWERFUL:
            return "o3-mini"
        elif tier == JevModelTier.REASONING:
            return "o1"
        return "gpt-4o-mini"

    def select_skills(self, decision: JevDecision) -> List[str]:
        """
        Returns only the minimal, relevant subset of skills recommended by JEV.
        """
        return decision.skills

    def context_budget(self, decision: JevDecision) -> int:
        """
        Returns the token budget ceiling for context assembly.
        """
        return decision.context_budget

    def _update_stats_for_decision(self, decision: JevDecision) -> None:
        self.stats.total_latency_ms += decision.latency_ms
        if decision.complexity == JevComplexity.SIMPLE:
            self.stats.simple_tasks += 1
        elif decision.complexity == JevComplexity.MEDIUM:
            self.stats.medium_tasks += 1
        elif decision.complexity == JevComplexity.ADVANCED:
            self.stats.advanced_tasks += 1


class JEVCapability:
    """
    Public Facade for Silvirica JEV Decision & Fast-Thinking Capability.
    Exposes stable, non-breaking methods for IDE and agent workflows.
    """

    _instance: Optional[JEVCapability] = None

    def __init__(self, config: Optional[JevConfig] = None, project_config: Optional[Any] = None):
        self.router = JevRouter(config=config, project_config=project_config)

    @classmethod
    def get_instance(cls, config: Optional[JevConfig] = None, project_config: Optional[Any] = None) -> JEVCapability:
        if cls._instance is None:
            cls._instance = cls(config=config, project_config=project_config)
        return cls._instance

    def classify(
        self,
        task: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
    ) -> JevComplexity:
        decision = self.router.evaluate_task(task, project_context, available_skills)
        return decision.complexity

    def route(
        self,
        task: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
        state_hash: str = "",
    ) -> JevDecision:
        return self.router.evaluate_task(
            task=task,
            project_context=project_context,
            available_skills=available_skills,
            state_hash=state_hash,
        )

    def select_skills(self, task: str, available_skills: Optional[List[str]] = None) -> List[str]:
        decision = self.router.evaluate_task(task, available_skills=available_skills)
        return self.router.select_skills(decision)

    def select_model(self, task: str) -> str:
        decision = self.router.evaluate_task(task)
        return self.router.select_model(decision)

    def context_budget(self, task: str) -> int:
        decision = self.router.evaluate_task(task)
        return self.router.context_budget(decision)

    def get_status(self) -> Dict[str, Any]:
        """
        Returns JEV capability diagnostic and health check data.
        """
        adapter = self.router.adapter
        breaker = adapter.circuit_breaker
        api_key = adapter.get_api_key()
        has_key = bool(api_key)

        return {
            "enabled": self.router.config.enabled,
            "mode": self.router.config.mode,
            "status": "Connected" if (self.router.config.enabled and breaker.state.value == "CLOSED") else "Degraded/Bypassed",
            "provider_endpoint": adapter.config.api_base,
            "api_key_configured": has_key,
            "circuit_breaker": breaker.get_stats(),
            "cache": self.router.cache.get_stats(),
            "stats": self.router.stats.to_dict(),
        }
