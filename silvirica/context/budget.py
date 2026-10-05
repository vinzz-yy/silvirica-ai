from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from silvirica.core.config import TokenBudgetConfig
from silvirica.core.types import ComplexityLevel, RiskLevel


@dataclass
class CategoryTokenBudget:
    total_budget: int
    code_budget: int
    memory_budget: int
    skills_budget: int
    errors_and_git_budget: int
    metadata_budget: int
    reserve_budget: int


class TokenBudgetManager:
    """
    Adaptive Category Token Budget Manager.
    Dynamically partitions the available context budget across
    Code, Memory, Skills, Error/Git traces, and Metadata.
    """

    def __init__(self, config: TokenBudgetConfig):
        self.config = config

    def calculate_budget(self, complexity: ComplexityLevel, risk: RiskLevel = RiskLevel.SAFE) -> int:
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

    def get_category_allocations(
        self, complexity: ComplexityLevel, risk: RiskLevel = RiskLevel.SAFE
    ) -> CategoryTokenBudget:
        total = self.calculate_budget(complexity, risk)

        # Adaptive percentage distribution based on task nature
        if complexity in [ComplexityLevel.LEVEL_0_INSTANT, ComplexityLevel.LEVEL_1_SIMPLE]:
            code_pct = 0.50
            mem_pct = 0.20
            skills_pct = 0.10
            err_pct = 0.10
            meta_pct = 0.05
        elif complexity in [ComplexityLevel.LEVEL_2_STANDARD, ComplexityLevel.LEVEL_3_COMPLEX]:
            code_pct = 0.60
            mem_pct = 0.15
            skills_pct = 0.10
            err_pct = 0.10
            meta_pct = 0.03
        else:  # Deep / Critical architecture tasks
            code_pct = 0.55
            mem_pct = 0.20
            skills_pct = 0.10
            err_pct = 0.10
            meta_pct = 0.03

        reserve_pct = max(0.02, 1.0 - (code_pct + mem_pct + skills_pct + err_pct + meta_pct))

        return CategoryTokenBudget(
            total_budget=total,
            code_budget=int(total * code_pct),
            memory_budget=int(total * mem_pct),
            skills_budget=int(total * skills_pct),
            errors_and_git_budget=int(total * err_pct),
            metadata_budget=int(total * meta_pct),
            reserve_budget=int(total * reserve_pct),
        )


# Backward compatibility alias
TokenBudgetEngine = TokenBudgetManager
