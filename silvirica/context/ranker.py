from __future__ import annotations
import re
from typing import List
from silvirica.core.types import ContextItem

class ContextRanker:
    @classmethod
    def rank_and_filter(cls, query: str, items: List[ContextItem], min_score: float = 0.20, max_items: int = 15) -> List[ContextItem]:
        query_terms = [t.lower() for t in re.findall(r'\w+', query) if len(t) > 2]
        if not query_terms:
            return items[:max_items]
        scored: List[ContextItem] = []
        for it in items:
            score = cls._calculate_score(query_terms, query, it)
            if score >= min_score:
                it.relevance_score = round(score, 3)
                scored.append(it)
        scored.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored[:max_items]

    @classmethod
    def _calculate_score(cls, query_terms: List[str], raw_query: str, item: ContextItem) -> float:
        content_lower = item.content.lower()
        ident_lower = item.identifier.lower()
        base_score = 0.0
        matches = sum(1 for t in query_terms if t in content_lower or t in ident_lower)
        overlap_ratio = matches / len(query_terms) if query_terms else 0.0
        base_score += overlap_ratio * 0.50
        for t in query_terms:
            if t == ident_lower or f"::{t}" in ident_lower:
                base_score += 0.35
                break
        if item.source_type == "symbol":
            base_score += 0.15
        elif item.source_type == "memory":
            base_score += 0.10
        return min(1.0, base_score)
