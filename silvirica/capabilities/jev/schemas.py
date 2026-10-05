from __future__ import annotations
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class JevComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    ADVANCED = "advanced"


class JevModelTier(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    POWERFUL = "powerful"
    REASONING = "reasoning"


class JevExecutionPath(str, Enum):
    FAST_PATH = "FAST_PATH"
    STANDARD_PATH = "STANDARD_PATH"
    DEEP_PATH = "DEEP_PATH"


@dataclass
class JevDecision:
    """
    Compact, structured decision emitted by JEV decision intelligence.
    Emits no prose/text — purely structured routing, complexity, skill selection,
    and context budget parameters.
    """
    complexity: JevComplexity = JevComplexity.MEDIUM
    confidence: float = 0.90
    route: str = "standard"
    skills: List[str] = field(default_factory=lambda: ["coding-core"])
    context_budget: int = 2500
    model_tier: JevModelTier = JevModelTier.STANDARD
    deep_reasoning: bool = False
    needs_escalation: bool = False
    execution_path: JevExecutionPath = JevExecutionPath.STANDARD_PATH
    latency_ms: float = 0.0
    source: str = "jev"  # jev, cache, native_fallback, circuit_breaker_fallback
    reasons: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "complexity": self.complexity.value if isinstance(self.complexity, JevComplexity) else self.complexity,
            "confidence": round(self.confidence, 3),
            "route": self.route,
            "skills": self.skills,
            "context_budget": self.context_budget,
            "model_tier": self.model_tier.value if isinstance(self.model_tier, JevModelTier) else self.model_tier,
            "deep_reasoning": self.deep_reasoning,
            "needs_escalation": self.needs_escalation,
            "execution_path": self.execution_path.value if isinstance(self.execution_path, JevExecutionPath) else self.execution_path,
            "latency_ms": round(self.latency_ms, 2),
            "source": self.source,
            "reasons": self.reasons,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JevDecision:
        comp_str = data.get("complexity", "medium")
        try:
            comp = JevComplexity(comp_str)
        except ValueError:
            comp = JevComplexity.MEDIUM

        tier_str = data.get("model_tier", "standard")
        try:
            tier = JevModelTier(tier_str)
        except ValueError:
            tier = JevModelTier.STANDARD

        path_str = data.get("execution_path", "STANDARD_PATH")
        try:
            path = JevExecutionPath(path_str)
        except ValueError:
            path = JevExecutionPath.STANDARD_PATH

        return cls(
            complexity=comp,
            confidence=float(data.get("confidence", 0.90)),
            route=str(data.get("route", "standard")),
            skills=list(data.get("skills", ["coding-core"])),
            context_budget=int(data.get("context_budget", 2500)),
            model_tier=tier,
            deep_reasoning=bool(data.get("deep_reasoning", False)),
            needs_escalation=bool(data.get("needs_escalation", False)),
            execution_path=path,
            latency_ms=float(data.get("latency_ms", 0.0)),
            source=str(data.get("source", "jev")),
            reasons=data.get("reasons"),
        )


@dataclass
class JevConfig:
    """
    Configuration for JEV Decision Engine.
    """
    enabled: bool = True
    mode: str = "fast"  # fast, balanced, deep
    timeout_ms: int = 500  # Strict latency budget ceiling
    fallback: str = "native"  # native, strict_error
    cache: bool = True
    model_routing: bool = True
    skill_routing: bool = True
    context_routing: bool = True
    api_base: str = "https://openrouter.ai/api/v1"
    api_key_env: str = "JEV_API_KEY"
    max_consecutive_failures: int = 3
    circuit_cooldown_seconds: float = 60.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JevConfig:
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)


@dataclass
class JevStats:
    total_decisions: int = 0
    cache_hits: int = 0
    jev_calls: int = 0
    native_fallbacks: int = 0
    circuit_trips: int = 0
    total_latency_ms: float = 0.0
    simple_tasks: int = 0
    medium_tasks: int = 0
    advanced_tasks: int = 0

    @property
    def average_latency_ms(self) -> float:
        if self.total_decisions == 0:
            return 0.0
        return round(self.total_latency_ms / self.total_decisions, 2)

    @property
    def cache_hit_rate(self) -> float:
        if self.total_decisions == 0:
            return 0.0
        return round((self.cache_hits / self.total_decisions) * 100, 1)

    @property
    def success_rate(self) -> float:
        if self.total_decisions == 0:
            return 100.0
        successful = self.total_decisions - self.native_fallbacks
        return round((max(0, successful) / self.total_decisions) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_pct": self.cache_hit_rate,
            "jev_calls": self.jev_calls,
            "native_fallbacks": self.native_fallbacks,
            "circuit_trips": self.circuit_trips,
            "average_latency_ms": self.average_latency_ms,
            "success_rate_pct": self.success_rate,
            "distribution": {
                "simple": self.simple_tasks,
                "medium": self.medium_tasks,
                "advanced": self.advanced_tasks,
            }
        }
