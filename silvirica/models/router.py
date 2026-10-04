from __future__ import annotations
from typing import Any, Dict, List, Optional
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import RoutingCategory, ComplexityLevel
from silvirica.models.providers import AIProvider, OpenAICompatibleProvider, LocalDeterministicProvider


class ModelRouter:
    """
    Intelligent Model Router.
    Routes tasks to the most cost-effective and accurate model category based on task classification.
    """

    def __init__(self, config: Optional[ProjectConfig] = None):
        self.config = config or ProjectConfig()
        self.providers: Dict[str, AIProvider] = {
            "openai_compatible": OpenAICompatibleProvider(self.config.providers.get("default", list(self.config.providers.values())[0])),
            "local": LocalDeterministicProvider(),
        }

    def select_category(self, complexity: ComplexityLevel, intent: str, risk: str) -> RoutingCategory:
        if risk == "CRITICAL" or complexity == ComplexityLevel.LEVEL_5_CRITICAL:
            return RoutingCategory.DEEP
        if intent in ["security_audit", "vulnerability_check"]:
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

    def get_model_for_category(self, category: RoutingCategory) -> str:
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
    ) -> Dict[str, Any]:
        model = self.get_model_for_category(category)
        if category == RoutingCategory.INSTANT or model == "local-deterministic":
            provider = self.providers["local"]
        else:
            provider = self.providers.get("openai_compatible", self.providers["local"])

        result = provider.generate(model=model, prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens)
        result["category"] = category.value
        return result
