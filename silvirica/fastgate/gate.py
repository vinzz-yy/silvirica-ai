from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from silvirica.core.types import ComplexityLevel, FastGateResult, RiskLevel
from silvirica.fastgate.classifier import FastGateClassifier
from silvirica.fastgate.zero_model import ZeroModelResolver
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.repository.symbols import SymbolIndex


class FastGate:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.zero_resolver = ZeroModelResolver(self.root_path)
        self.symbol_index = SymbolIndex(self.root_path / ".silvirica" / "symbols" / "symbols.db")
        self.vault = ObsidianMemoryVault(self.root_path / ".silvirica" / "memory")

    def process(self, query: str) -> FastGateResult:
        is_zero, reason, answer = self.zero_resolver._resolve_internal(query)
        if is_zero and answer is not None:
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
            )

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
        )

    @classmethod
    def evaluate(
        cls,
        query: str,
        root_path: Path,
        symbol_index: Optional[SymbolIndex] = None,
        memory_vault: Optional[ObsidianMemoryVault] = None,
        graph_engine: Optional[Any] = None,
    ) -> FastGateResult:
        gate = cls(root_path)
        if symbol_index:
            gate.symbol_index = symbol_index
            gate.zero_resolver.symbol_index = symbol_index
        if memory_vault:
            gate.vault = memory_vault
            gate.zero_resolver.vault = memory_vault
        return gate.process(query)
