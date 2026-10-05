from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from silvirica.core.types import ContextItem


@dataclass
class ContextQualityBreakdown:
    exact_symbol_relevance: float = 0.0
    dependency_relevance: float = 0.0
    caller_callee_relevance: float = 0.0
    route_relevance: float = 0.0
    database_relevance: float = 0.0
    git_relevance: float = 0.0
    error_stack_relevance: float = 0.0
    memory_relevance: float = 0.0
    semantic_relevance: float = 0.0
    overall_quality_score: float = 0.0


class ContextRanker:
    """
    Hierarchical context quality scorer and ranker.
    Calculates multi-dimensional ContextQualityScore across:
    1. Exact symbol relevance
    2. Direct dependencies (imports, extends, uses)
    3. Caller / callee call hierarchy
    4. Route & API endpoint mappings
    5. Database & schema entities
    6. Git change & recent modification diffs
    7. Error stack traces & failure signals
    8. Verified project memory (ADRs, conventions, fixes)
    9. Semantic & lexical keyword overlap
    """

    PRIORITY_WEIGHTS = {
        "exact_symbol": 1.00,
        "symbol": 0.85,
        "dependency": 0.75,
        "caller": 0.70,
        "callee": 0.65,
        "route": 0.70,
        "database": 0.68,
        "memory": 0.60,
        "convention": 0.50,
        "git_diff": 0.55,
        "nearby_code": 0.40,
        "generic": 0.30,
    }

    @classmethod
    def rank_and_filter(
        cls, query: str, items: List[ContextItem], min_score: float = 0.15, max_items: int = 15
    ) -> List[ContextItem]:
        query_terms = [t.lower() for t in re.findall(r'\w+', query) if len(t) > 2]
        if not items:
            return []

        scored: List[ContextItem] = []
        for it in items:
            breakdown = cls.score_item(query, it, query_terms)
            if breakdown.overall_quality_score >= min_score:
                it.relevance_score = round(breakdown.overall_quality_score, 3)
                scored.append(it)

        scored.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored[:max_items]

    @classmethod
    def score_item(
        cls, raw_query: str, item: ContextItem, query_terms: Optional[List[str]] = None
    ) -> ContextQualityBreakdown:
        if query_terms is None:
            query_terms = [t.lower() for t in re.findall(r'\w+', raw_query) if len(t) > 2]

        content_lower = item.content.lower()
        ident_lower = item.identifier.lower()
        source_type = item.source_type.lower()
        query_lower = raw_query.lower()

        # 1. Lexical & semantic overlap
        if query_terms:
            matches = sum(1 for t in query_terms if t in content_lower or t in ident_lower)
            semantic_score = matches / len(query_terms)
        else:
            semantic_score = 0.5

        # 2. Exact symbol relevance
        exact_symbol = 0.0
        for t in query_terms:
            if t == ident_lower or f"::{t}" in ident_lower or f"/{t}." in ident_lower or f"class {t}" in content_lower:
                exact_symbol = 1.0
                break

        # 3. Direct dependency relevance
        dep_score = 0.85 if source_type in ["dependency", "import", "extends"] and any(t in content_lower for t in query_terms) else 0.0

        # 4. Caller / callee relevance
        caller_callee = 0.80 if source_type in ["caller", "callee", "call_graph"] and any(t in content_lower for t in query_terms) else 0.0

        # 5. Route relevance
        route_score = 0.75 if source_type == "route" or any(r in query_lower for r in ["route", "endpoint", "api", "url"]) and "route" in content_lower else 0.0

        # 6. Database relevance
        db_score = 0.75 if source_type in ["database", "schema", "model"] and any(d in query_lower for d in ["db", "sql", "migration", "query", "schema", "table"]) else 0.0

        # 7. Git relevance
        git_score = 0.0
        if "git" in source_type:
            if any(b in query_lower for b in ["bug", "fix", "error", "fail", "broke", "recent", "why"]):
                git_score = 0.90
            else:
                git_score = 0.50

        # 8. Error / stack trace relevance
        error_score = 0.0
        if any(e in query_lower for e in ["error", "traceback", "exception", "crash", "stack"]):
            if any(e in content_lower for e in ["traceback", "exception", "raise", "error", "line "]):
                error_score = 0.85

        # 9. Memory relevance
        mem_score = 0.80 if source_type == "memory" or "decision" in source_type else 0.0

        # Composite overall quality calculation
        base_weight = cls.PRIORITY_WEIGHTS.get(source_type, 0.40)
        overall = (
            (base_weight * 0.30)
            + (semantic_score * 0.25)
            + (exact_symbol * 0.20)
            + (git_score * 0.10)
            + (dep_score * 0.05)
            + (caller_callee * 0.05)
            + (error_score * 0.05)
        )
        overall_clamped = min(1.0, max(0.0, overall))

        return ContextQualityBreakdown(
            exact_symbol_relevance=round(exact_symbol, 2),
            dependency_relevance=round(dep_score, 2),
            caller_callee_relevance=round(caller_callee, 2),
            route_relevance=round(route_score, 2),
            database_relevance=round(db_score, 2),
            git_relevance=round(git_score, 2),
            error_stack_relevance=round(error_score, 2),
            memory_relevance=round(mem_score, 2),
            semantic_relevance=round(semantic_score, 2),
            overall_quality_score=round(overall_clamped, 3),
        )

    @classmethod
    def calculate_context_confidence(
        cls, task: str, compiled_items: List[ContextItem], symbols: Optional[List[str]] = None
    ) -> float:
        """
        Estimates the Context Confidence Score (0.0 to 1.0).
        High confidence (>0.80) indicates all relevant symbols, dependencies, and context are present.
        Low confidence (<0.70) triggers automatic adaptive context expansion.
        """
        if not task:
            return 0.5

        query_terms = [t.lower() for t in re.findall(r'\w+', task) if len(t) > 2]
        if not query_terms:
            return 0.80

        # Check symbol coverage
        symbol_covered = False
        if symbols:
            for s in symbols:
                if any(t in s.lower() for t in query_terms):
                    symbol_covered = True
                    break

        item_max_score = max((it.relevance_score for it in compiled_items), default=0.0)
        coverage_ratio = sum(
            1 for t in query_terms if any(t in (it.content.lower() + it.identifier.lower()) for it in compiled_items)
        ) / len(query_terms)

        confidence = (0.40 * (1.0 if symbol_covered else 0.40)) + (0.35 * item_max_score) + (0.25 * coverage_ratio)
        return round(min(1.0, max(0.10, confidence)), 2)
