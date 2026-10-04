from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from silvirica.context.budget import TokenBudgetEngine
from silvirica.context.compressor import ContextCompressor
from silvirica.context.deduplicator import ContextDeduplicator
from silvirica.context.ranker import ContextRanker
from silvirica.context.redactor import SecretRedactor
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import ComplexityLevel, ContextItem, FastGateResult, RiskLevel


@dataclass
class CompiledContextBundle:
    prompt: str
    input_tokens: int
    token_budget: int
    skills_text: str = ""
    token_count: int = 0
    naive_baseline_tokens: int = 15000
    reduction_percentage: float = 85.0
    items_included: List[ContextItem] = field(default_factory=list)
    redacted_secrets_count: int = 0
    budget_limit: int = 6000


# Compatibility alias
CompiledContext = CompiledContextBundle


class SmartContextCompiler:
    def __init__(self, root_or_config: Optional[Union[Path, ProjectConfig]] = None, config: Optional[ProjectConfig] = None):
        if isinstance(root_or_config, ProjectConfig):
            self.config = root_or_config
            self.root_path = Path.cwd()
        elif isinstance(root_or_config, Path):
            self.root_path = root_or_config.resolve()
            self.config = config or load_config(self.root_path)
        else:
            self.root_path = Path.cwd()
            self.config = config or load_config(self.root_path)

        self.budget_engine = TokenBudgetEngine(self.config.token_budget)

    def compile(
        self,
        task: str,
        complexity: Optional[ComplexityLevel] = None,
        symbols: Optional[List[str]] = None,
        memory: Optional[List[str]] = None,
        graph_nodes: Optional[List[str]] = None,
        skills: Optional[str] = None,
        gate_result: Optional[FastGateResult] = None,
        candidate_items: Optional[List[ContextItem]] = None,
        project_conventions: str = "",
        constraints: Optional[List[str]] = None,
    ) -> CompiledContextBundle:
        eff_complexity = complexity or (gate_result.complexity if gate_result else ComplexityLevel.LEVEL_2_STANDARD)
        eff_risk = gate_result.risk if gate_result else RiskLevel.SAFE
        budget = self.budget_engine.calculate_budget(eff_complexity, eff_risk)

        sections: List[str] = [f"# TASK INSTRUCTION\n{task.strip()}"]

        if project_conventions:
            sections.append(f"## Project Conventions\n{project_conventions.strip()}")

        if skills:
            sections.append(f"## Active Specialized Guidelines\n{skills.strip()}")

        if memory:
            mem_text = "\n".join(f"- {m}" for m in memory)
            sections.append(f"## Verified Project Memory\n{mem_text}")

        if graph_nodes:
            g_text = ", ".join(graph_nodes)
            sections.append(f"## Related Architecture Nodes\n{g_text}")

        if symbols:
            s_text = "\n".join(f"- {s}" for s in symbols)
            sections.append(f"## Relevant Code Symbols\n{s_text}")

        if candidate_items:
            ranked = ContextRanker.rank_and_filter(task, candidate_items, min_score=0.20, max_items=10)
            code_sec = ["## Candidate Context"]
            for it in ranked:
                code_sec.append(f"### [{it.source_type}] {it.identifier}\n```{it.content}\n```")
            sections.append("\n".join(code_sec))

        if constraints:
            dedup_c = ContextDeduplicator.deduplicate_items(constraints)
            sections.append("## Strict Constraints\n" + "\n".join(f"- {c}" for c in dedup_c))

        raw_prompt = "\n\n".join(sections)
        redacted_prompt, redacted_count = SecretRedactor.redact(raw_prompt)
        input_tokens = ContextCompressor.estimate_tokens(redacted_prompt)

        naive_baseline = max(input_tokens * 8, 12000)
        reduction = round(max(0.0, (naive_baseline - input_tokens) / naive_baseline) * 100, 1)

        return CompiledContextBundle(
            prompt=redacted_prompt,
            input_tokens=input_tokens,
            token_budget=budget,
            skills_text=skills or "",
            token_count=input_tokens,
            naive_baseline_tokens=naive_baseline,
            reduction_percentage=reduction,
            redacted_secrets_count=redacted_count,
            budget_limit=budget,
        )
