from __future__ import annotations
from silvirica.core.config import TokenBudgetConfig
from silvirica.core.types import ComplexityLevel, RiskLevel

class TokenBudgetEngine:
    def __init__(self, config: TokenBudgetConfig):
        self.config = config

    def calculate_budget(self, complexity: ComplexityLevel, risk: RiskLevel) -> int:
        if complexity == ComplexityLevel.LEVEL_0_INSTANT:
            return self.config.trivial_task_max_tokens
        elif complexity == ComplexityLevel.LEVEL_1_SIMPLE:
            return self.config.simple_task_max_tokens
        elif complexity == ComplexityLevel.LEVEL_2_STANDARD:
            return self.config.standard_task_max_tokens
        elif complexity == ComplexityLevel.LEVEL_3_COMPLEX:
            return self.config.complex_task_max_tokens
        elif complexity == ComplexityLevel.LEVEL_4_DEEP:
            return self.config.deep_task_max_tokens
        else:
            return self.config.max_context_tokens
