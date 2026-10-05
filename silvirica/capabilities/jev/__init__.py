"""
Silvirica JEV Decision & Fast-Thinking Capability Module.
TypeSafe System One fast decision layer for sub-millisecond task classification,
skill routing, context budgeting, and model tiering.
"""

from silvirica.capabilities.jev.adapter import JevAdapter
from silvirica.capabilities.jev.cache import JevDecisionCache
from silvirica.capabilities.jev.circuit_breaker import CircuitState, JevCircuitBreaker
from silvirica.capabilities.jev.classifier import JevTaskClassifier
from silvirica.capabilities.jev.fallback import NativeFallbackRouter
from silvirica.capabilities.jev.router import JEVCapability, JevRouter
from silvirica.capabilities.jev.schemas import (
    JevComplexity,
    JevConfig,
    JevDecision,
    JevExecutionPath,
    JevModelTier,
    JevStats,
)

__all__ = [
    "JEVCapability",
    "JevRouter",
    "JevAdapter",
    "JevTaskClassifier",
    "JevCircuitBreaker",
    "CircuitState",
    "JevDecisionCache",
    "NativeFallbackRouter",
    "JevDecision",
    "JevConfig",
    "JevStats",
    "JevComplexity",
    "JevModelTier",
    "JevExecutionPath",
]
