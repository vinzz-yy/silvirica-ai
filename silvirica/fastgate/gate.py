from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from silvirica.cache.engine import CacheTier, MultiTierCacheManager
from silvirica.core.types import ComplexityLevel, FastGateResult, RiskLevel
from silvirica.fastgate.classifier import FastGateClassifier
from silvirica.fastgate.zero_model import ZeroModelResolver
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.repository.symbols import SymbolIndex


class FastGate:
    def __init__(self, root_path: Path, cache_manager: Optional[MultiTierCacheManager] = None):
        self.root_path = root_path.resolve()
        self.silvirica_dir = self.root_path / ".silvirica"
        self.cache = cache_manager or MultiTierCacheManager(self.silvirica_dir / "cache")
        self.zero_resolver = ZeroModelResolver(self.root_path, self.cache)
        self.symbol_index = SymbolIndex(self.silvirica_dir / "symbols" / "symbols.db")
        self.vault = ObsidianMemoryVault(self.silvirica_dir / "memory")

    def process(self, query: str, state_hash: str = "") -> FastGateResult:
        # 1. Check L1 Request Cache
        cache_key = MultiTierCacheManager.generate_key(CacheTier.L1_REQUEST, query.strip().lower())
        cached_res = self.cache.get(CacheTier.L1_REQUEST, cache_key, current_state_hash=state_hash)
        if cached_res and isinstance(cached_res, dict):
            return FastGateResult(
                intent=cached_res.get("intent", "cached_lookup"),
                complexity=ComplexityLevel(cached_res.get("complexity", 0)),
                risk=RiskLevel(cached_res.get("risk", "SAFE")),
                skills_matched=cached_res.get("skills_matched", []),
                likely_tools=cached_res.get("likely_tools", []),
                likely_files=cached_res.get("likely_files", []),
                is_zero_model=cached_res.get("is_zero_model", True),
                zero_model_reason="L1 Request Cache Hit (0 LLM Tokens)",
                zero_model_answer=cached_res.get("zero_model_answer"),
                zero_model_result=cached_res.get("zero_model_result"),
                reasoning_budget_tokens=0,
                cache_hit=True,
                cached_response=cached_res.get("zero_model_result"),
            )

        # 2. Check Zero-Model Resolver
        is_zero, reason, answer = self.zero_resolver._resolve_internal(query)
        if is_zero and answer is not None:
            # Store in L1 cache
            self.cache.set(
                CacheTier.L1_REQUEST,
                cache_key,
                {
                    "intent": "zero_model_lookup",
                    "complexity": int(ComplexityLevel.LEVEL_0_INSTANT),
                    "risk": RiskLevel.SAFE.value,
                    "skills_matched": [],
                    "likely_tools": ["symbol_index"],
                    "likely_files": [],
                    "is_zero_model": True,
                    "zero_model_reason": reason,
                    "zero_model_answer": answer,
                    "zero_model_result": answer,
                },
                project_state_hash=state_hash,
            )
            return FastGateResult(
                intent="zero_model_lookup",
                complexity=ComplexityLevel.LEVEL_0_INSTANT,
                risk=RiskLevel.SAFE,
                skills_matched=[],
                likely_tools=["symbol_index"],
                likely_files=[],
                is_zero_model=True,
                zero_model_reason=reason,
                zero_model_answer=answer,
                zero_model_result=answer,
                reasoning_budget_tokens=0,
                cache_hit=False,
            )

        # 3. FastGate Intent Classification
        clf = FastGateClassifier.classify(query)
        intent = clf["intent"]
        complexity = clf["complexity"]
        risk = clf["risk"]
        skills = clf["skills"]
        budget = clf["reasoning_budget"]

        likely_files = []
        words = [w for w in query.split() if len(w) > 3]
        for w in words[:3]:
            matches = self.symbol_index.find_by_name(w)
            for m in matches:
                if m.file_path not in likely_files:
                    likely_files.append(m.file_path)

        likely_tools = ["ast_retriever", "context_compiler"]
        if "security-audit" in skills or risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            likely_tools.append("security_scanner")

        return FastGateResult(
            intent=intent,
            complexity=complexity,
            risk=risk,
            skills_matched=skills,
            likely_tools=likely_tools,
            likely_files=likely_files[:5],
            is_zero_model=False,
            reasoning_budget_tokens=budget,
            cache_hit=False,
        )

    @classmethod
    def evaluate(
        cls,
        query: str,
        root_path: Path,
        symbol_index: Optional[SymbolIndex] = None,
        memory_vault: Optional[ObsidianMemoryVault] = None,
        graph_engine: Optional[Any] = None,
        cache_manager: Optional[MultiTierCacheManager] = None,
        state_hash: str = "",
    ) -> FastGateResult:
        gate = cls(root_path, cache_manager=cache_manager)
        if symbol_index:
            gate.symbol_index = symbol_index
            gate.zero_resolver.symbol_index = symbol_index
        if memory_vault:
            gate.vault = memory_vault
            gate.zero_resolver.vault = memory_vault
        return gate.process(query, state_hash=state_hash)
