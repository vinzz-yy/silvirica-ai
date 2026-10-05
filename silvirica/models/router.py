from __future__ import annotations
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from silvirica.cache.engine import CacheTier, MultiTierCacheManager
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import ComplexityLevel, RoutingCategory
from silvirica.models.escalation import EscalationManager
from silvirica.models.outcome import OutcomeEngine, TaskOutcome
from silvirica.models.providers import AIProvider, LocalDeterministicProvider, OpenAICompatibleProvider
from silvirica.models.validator import ResultValidator


class ModelRouter:
    """
    Intelligent Model Router & Auto-Escalation Engine 2.0.
    - Routes tasks to the cheapest capable model tier.
    - Utilizes empirical model performance history from OutcomeEngine.
    - Utilizes L7 Model Response Cache.
    - Validates code results with ResultValidator and escalates automatically if syntax or requirements fail.
    - Persists verified outcomes into OutcomeEngine.
    """

    def __init__(
        self,
        config: Optional[ProjectConfig] = None,
        cache_manager: Optional[MultiTierCacheManager] = None,
        outcome_engine: Optional[OutcomeEngine] = None,
    ):
        self.config = config or ProjectConfig()
        self.cache = cache_manager or MultiTierCacheManager(Path.cwd() / ".silvirica" / "cache")
        self.outcome_engine = outcome_engine or OutcomeEngine()
        self.providers: Dict[str, AIProvider] = {
            "openai_compatible": OpenAICompatibleProvider(
                self.config.providers.get("default", list(self.config.providers.values())[0])
            ),
            "local": LocalDeterministicProvider(),
        }

    def select_category(self, complexity: ComplexityLevel, intent: str, risk: str) -> RoutingCategory:
        if risk == "CRITICAL" or complexity == ComplexityLevel.LEVEL_5_CRITICAL:
            return RoutingCategory.DEEP
        if intent in ["security_audit", "vulnerability_check", "critical_security_analysis"]:
            return RoutingCategory.SECURITY
        if intent in ["architecture_review", "system_design"]:
            return RoutingCategory.ARCHITECT
        if intent in ["uiux_review", "frontend_design"]:
            return RoutingCategory.VISUAL
        if complexity == ComplexityLevel.LEVEL_0_INSTANT:
            return RoutingCategory.INSTANT
        if complexity == ComplexityLevel.LEVEL_1_SIMPLE:
            return RoutingCategory.QUICK
        if complexity == ComplexityLevel.LEVEL_2_STANDARD:
            return RoutingCategory.STANDARD
        if complexity == ComplexityLevel.LEVEL_3_COMPLEX:
            return RoutingCategory.CODER
        if complexity == ComplexityLevel.LEVEL_4_DEEP:
            return RoutingCategory.DEEP
        return RoutingCategory.STANDARD

    def get_model_for_category(self, category: RoutingCategory, intent: str = "") -> str:
        # Check empirical best model from OutcomeEngine
        if intent:
            best_model = self.outcome_engine.get_best_model_for_task(intent)
            if best_model:
                return best_model

        routing = self.config.routing
        mapping = {
            RoutingCategory.INSTANT: routing.instant_model,
            RoutingCategory.QUICK: routing.quick_model,
            RoutingCategory.STANDARD: routing.standard_model,
            RoutingCategory.CODER: routing.coder_model,
            RoutingCategory.DEEP: routing.deep_model,
            RoutingCategory.ARCHITECT: routing.architect_model,
            RoutingCategory.SECURITY: routing.security_model,
            RoutingCategory.VISUAL: routing.visual_model,
            RoutingCategory.RESEARCH: routing.research_model,
            RoutingCategory.ULTRABRAIN: routing.ultrabrain_model,
            RoutingCategory.LOCAL: routing.local_model,
        }
        return mapping.get(category, routing.standard_model)

    def execute_routing(
        self,
        category: RoutingCategory,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        task: str = "",
        state_hash: str = "",
        allow_cache: bool = True,
        auto_escalate: bool = True,
        max_escalations: int = 2,
    ) -> Dict[str, Any]:
        model = self.get_model_for_category(category)

        # 1. Check L7 Model Response Cache
        if allow_cache:
            cache_key = MultiTierCacheManager.generate_key(CacheTier.L7_MODEL_RESPONSE, model, prompt)
            cached_resp = self.cache.get(CacheTier.L7_MODEL_RESPONSE, cache_key, current_state_hash=state_hash)
            if cached_resp and isinstance(cached_resp, dict):
                cached_resp["cache_hit"] = True
                return cached_resp

        # 2. Select Provider
        if category == RoutingCategory.INSTANT or model == "local-deterministic":
            provider = self.providers["local"]
        else:
            provider = self.providers.get("openai_compatible", self.providers["local"])

        # 3. Execution
        result = provider.generate(
            model=model, prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens
        )
        result["category"] = category.value
        result["cache_hit"] = False
        result["escalations"] = 0

        # 4. Result Validation & Auto-Escalation
        val = ResultValidator.validate_response(result.get("text", ""), task=task)
        if auto_escalate and max_escalations > 0:
            if val.needs_escalation and category in [RoutingCategory.QUICK, RoutingCategory.STANDARD, RoutingCategory.CODER]:
                handoff = EscalationManager.create_handoff(
                    task=task or "Resolve code error",
                    evidence=val.errors,
                    failed_attempts=[f"Model {model} failed validation: {val.escalation_reason}"],
                    current_category=category,
                )
                escalated_prompt = handoff.to_prompt() + "\n\n" + prompt
                escalated_category = handoff.target_category

                escalated_result = self.execute_routing(
                    category=escalated_category,
                    prompt=escalated_prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    task=task,
                    state_hash=state_hash,
                    allow_cache=False,
                    auto_escalate=False,
                )
                escalated_result["escalations"] = 1
                escalated_result["previous_model"] = model
                escalated_result["escalation_reason"] = val.escalation_reason
                
                # Record outcome
                self.outcome_engine.record_outcome(
                    TaskOutcome(
                        task_id=str(uuid.uuid4())[:8],
                        task_type=category.value,
                        task_description=task,
                        context_tokens=len(prompt) // 4,
                        skills_selected=[],
                        model_selected=escalated_result.get("model", model),
                        validation_passed=True,
                        escalated=True,
                        latency_seconds=escalated_result.get("latency", 0.0),
                    )
                )
                return escalated_result

        # Record outcome
        self.outcome_engine.record_outcome(
            TaskOutcome(
                task_id=str(uuid.uuid4())[:8],
                task_type=category.value,
                task_description=task,
                context_tokens=len(prompt) // 4,
                skills_selected=[],
                model_selected=model,
                validation_passed=val.is_valid,
                escalated=False,
                latency_seconds=result.get("latency", 0.0),
            )
        )

        # Store in L7 Cache if success
        if result.get("success") and allow_cache and val.is_valid:
            cache_key = MultiTierCacheManager.generate_key(CacheTier.L7_MODEL_RESPONSE, model, prompt)
            self.cache.set(
                CacheTier.L7_MODEL_RESPONSE,
                cache_key,
                result,
                project_state_hash=state_hash,
                ttl_seconds=86400,
            )

        return result
