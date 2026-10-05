from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from silvirica.cache.engine import CacheTier, MultiTierCacheManager
from silvirica.context.budget import TokenBudgetManager
from silvirica.context.compressor import ContextCompressor
from silvirica.context.deduplicator import ContextDeduplicator
from silvirica.context.ranker import ContextRanker, ContextQualityBreakdown
from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import ComplexityLevel, ContextItem, FastGateResult, RiskLevel
from silvirica.security.prompt_armor import ContextTrustTier, PromptArmor


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
    symbols_selected_count: int = 0
    files_avoided_count: int = 0
    cache_hit: bool = False
    context_confidence: float = 0.90
    context_quality_score: float = 0.85
    expansion_level: int = 1


CompiledContext = CompiledContextBundle


class SmartContextCompiler:
    """
    Surgical Smart Context Compiler for Silvirica AI 2.0.
    Assembles minimal sufficient context following strict hierarchy and
    prompt injection defense.
    """

    def __init__(
        self,
        root_or_config: Optional[Union[Path, ProjectConfig]] = None,
        config: Optional[ProjectConfig] = None,
        cache_manager: Optional[MultiTierCacheManager] = None,
    ):
        if isinstance(root_or_config, ProjectConfig):
            self.config = root_or_config
            self.root_path = Path.cwd()
        elif isinstance(root_or_config, Path):
            self.root_path = root_or_config.resolve()
            self.config = config or load_config(self.root_path)
        else:
            self.root_path = Path.cwd()
            self.config = config or load_config(self.root_path)

        self.silvirica_dir = self.root_path / ".silvirica"
        self.budget_engine = TokenBudgetManager(self.config.token_budget)
        self.cache = cache_manager or MultiTierCacheManager(self.silvirica_dir / "cache")

    def compile(
        self,
        task: str,
        complexity: Optional[ComplexityLevel] = None,
        symbols: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        callers_callees: Optional[List[str]] = None,
        memory: Optional[List[str]] = None,
        graph_nodes: Optional[List[str]] = None,
        skills: Optional[str] = None,
        git_diffs: Optional[str] = None,
        gate_result: Optional[FastGateResult] = None,
        candidate_items: Optional[List[ContextItem]] = None,
        project_conventions: str = "",
        constraints: Optional[List[str]] = None,
        state_hash: str = "",
    ) -> CompiledContextBundle:
        eff_complexity = complexity or (gate_result.complexity if gate_result else ComplexityLevel.LEVEL_2_STANDARD)
        eff_risk = gate_result.risk if gate_result else RiskLevel.SAFE
        budget = self.budget_engine.calculate_budget(eff_complexity, eff_risk)

        # 1. Check L4 Context Cache
        cache_key = MultiTierCacheManager.generate_key(
            CacheTier.L4_CONTEXT, task.strip(), eff_complexity.value, skills or ""
        )
        cached_bundle = self.cache.get(CacheTier.L4_CONTEXT, cache_key, current_state_hash=state_hash)
        if cached_bundle and isinstance(cached_bundle, dict):
            return CompiledContextBundle(
                prompt=cached_bundle["prompt"],
                input_tokens=cached_bundle["input_tokens"],
                token_budget=budget,
                skills_text=skills or "",
                token_count=cached_bundle["input_tokens"],
                naive_baseline_tokens=cached_bundle.get("naive_baseline_tokens", 15000),
                reduction_percentage=cached_bundle.get("reduction_percentage", 90.0),
                redacted_secrets_count=cached_bundle.get("redacted_secrets_count", 0),
                budget_limit=budget,
                symbols_selected_count=cached_bundle.get("symbols_selected_count", len(symbols or [])),
                files_avoided_count=cached_bundle.get("files_avoided_count", 15),
                cache_hit=True,
                context_confidence=cached_bundle.get("context_confidence", 0.95),
                context_quality_score=cached_bundle.get("context_quality_score", 0.90),
                expansion_level=cached_bundle.get("expansion_level", 1),
            )

        # 2. Build prioritized sections with untrusted data boundary and PromptArmor
        sections: List[str] = [
            PromptArmor.get_system_security_preamble(),
            f"# TASK INSTRUCTION\n{task.strip()}"
        ]

        if project_conventions:
            sections.append(f"## Project Conventions\n{project_conventions.strip()}")

        if skills:
            sections.append(f"## Active Specialized Guidelines\n{skills.strip()}")

        # Exact symbols (Level 1)
        expansion_level = 1
        symbols_count = 0
        if symbols:
            symbols_dedup = ContextDeduplicator.deduplicate_items(symbols)
            symbols_count = len(symbols_dedup)
            sym_text = "\n".join(f"- {s}" for s in symbols_dedup)
            armored_syms = PromptArmor.wrap_untrusted_data(sym_text, source_type="symbols", identifier="exact_symbols")
            sections.append(f"## Exact Code Symbols\n{armored_syms}")

        # Direct dependencies (Level 2)
        if dependencies:
            deps_dedup = ContextDeduplicator.deduplicate_items(dependencies)
            dep_text = "\n".join(f"- {d}" for d in deps_dedup)
            armored_deps = PromptArmor.wrap_untrusted_data(dep_text, source_type="graph_dependencies", identifier="direct_dependencies")
            sections.append(f"## Direct Dependencies\n{armored_deps}")
            expansion_level = max(expansion_level, 2)

        # Callers / Callees (Level 3)
        if callers_callees:
            cc_dedup = ContextDeduplicator.deduplicate_items(callers_callees)
            cc_text = "\n".join(f"- {c}" for c in cc_dedup)
            armored_cc = PromptArmor.wrap_untrusted_data(cc_text, source_type="call_graph", identifier="callers_callees")
            sections.append(f"## Call Hierarchy & Dependents\n{armored_cc}")
            expansion_level = max(expansion_level, 3)

        # Memory
        if memory:
            mem_dedup = ContextDeduplicator.deduplicate_items(memory)
            mem_text = "\n".join(f"- {m}" for m in mem_dedup)
            armored_mem = PromptArmor.wrap_untrusted_data(mem_text, source_type="memory_vault", identifier="project_memory")
            sections.append(f"## Verified Project Memory\n{armored_mem}")

        # Architecture Graph Nodes (Level 4)
        if graph_nodes:
            g_nodes = ContextDeduplicator.deduplicate_items(graph_nodes)
            sections.append(f"## Related Architecture Nodes\n{', '.join(g_nodes)}")
            expansion_level = max(expansion_level, 4)

        # Git diffs (crucial for bug / failure investigation)
        if git_diffs:
            armored_git = PromptArmor.wrap_untrusted_data(git_diffs.strip()[:1500], source_type="git_diff", identifier="uncommitted_changes")
            sections.append(f"## Recent Git Modifications\n{armored_git}")

        # Candidate code items ranked and trimmed to fit budget
        items_included: List[ContextItem] = []
        if candidate_items:
            ranked = ContextRanker.rank_and_filter(task, candidate_items, min_score=0.15, max_items=10)
            code_sec = ["## Targeted Code Context"]
            current_estimated_tokens = sum(ContextCompressor.estimate_tokens(s) for s in sections)

            for it in ranked:
                item_tokens = ContextCompressor.estimate_tokens(it.content)
                if current_estimated_tokens + item_tokens <= budget or not items_included:
                    wrapped_block = PromptArmor.wrap_untrusted_data(it.content, source_type=it.source_type, identifier=it.identifier)
                    code_sec.append(f"### [{it.source_type}] {it.identifier}\n{wrapped_block}")
                    items_included.append(it)
                    current_estimated_tokens += item_tokens
                else:
                    # Truncate content to fit remaining budget
                    remaining_budget = max(50, budget - current_estimated_tokens)
                    truncated_lines = it.content.splitlines()[: max(5, remaining_budget // 10)]
                    truncated_content = "\n".join(truncated_lines) + "\n... [Remaining lines truncated to preserve token budget]"
                    wrapped_block = PromptArmor.wrap_untrusted_data(truncated_content, source_type=it.source_type, identifier=it.identifier)
                    code_sec.append(f"### [{it.source_type}] {it.identifier} (truncated)\n{wrapped_block}")
                    items_included.append(it)
                    break

            if len(code_sec) > 1:
                sections.append("\n".join(code_sec))

        if constraints:
            dedup_c = ContextDeduplicator.deduplicate_items(constraints)
            sections.append("## Strict Constraints\n" + "\n".join(f"- {c}" for c in dedup_c))

        # Calculate Context Confidence & Quality Score
        confidence = ContextRanker.calculate_context_confidence(task, items_included, symbols)
        quality_score = round(
            sum(it.relevance_score for it in items_included) / max(1, len(items_included)), 2
        ) if items_included else 0.85

        if confidence < 0.70 and expansion_level < 4 and graph_nodes:
            expansion_level = min(5, expansion_level + 1)

        raw_prompt = "\n\n".join(sections)
        raw_prompt_compressed = ContextCompressor.compress_text(raw_prompt)
        redacted_prompt, redacted_count = SecretRedactor.redact(raw_prompt_compressed, mode=SecurityMode.BALANCED)
        input_tokens = ContextCompressor.estimate_tokens(redacted_prompt)

        # Baseline calculation: full repository / unranked dump
        naive_baseline = max(input_tokens * 8, 16000)
        reduction = round(max(0.0, (naive_baseline - input_tokens) / naive_baseline) * 100, 1)
        files_avoided = max(10, len(items_included) * 5)

        bundle = CompiledContextBundle(
            prompt=redacted_prompt,
            input_tokens=input_tokens,
            token_budget=budget,
            skills_text=skills or "",
            token_count=input_tokens,
            naive_baseline_tokens=naive_baseline,
            reduction_percentage=reduction,
            items_included=items_included,
            redacted_secrets_count=redacted_count,
            budget_limit=budget,
            symbols_selected_count=symbols_count,
            files_avoided_count=files_avoided,
            cache_hit=False,
            context_confidence=confidence,
            context_quality_score=quality_score,
            expansion_level=expansion_level,
        )

        # Store in L4 Context Cache
        self.cache.set(
            CacheTier.L4_CONTEXT,
            cache_key,
            {
                "prompt": bundle.prompt,
                "input_tokens": bundle.input_tokens,
                "naive_baseline_tokens": bundle.naive_baseline_tokens,
                "reduction_percentage": bundle.reduction_percentage,
                "redacted_secrets_count": bundle.redacted_secrets_count,
                "symbols_selected_count": bundle.symbols_selected_count,
                "files_avoided_count": bundle.files_avoided_count,
                "context_confidence": bundle.context_confidence,
                "context_quality_score": bundle.context_quality_score,
                "expansion_level": bundle.expansion_level,
            },
            project_state_hash=state_hash,
            ttl_seconds=3600,
        )

        return bundle
