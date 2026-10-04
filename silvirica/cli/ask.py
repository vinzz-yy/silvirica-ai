from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from silvirica.context.compiler import SmartContextCompiler
from silvirica.core.config import load_config
from silvirica.core.project import ProjectBrain
from silvirica.core.types import ComplexityLevel, RoutingCategory, TelemetryEvent
from silvirica.fastgate.gate import FastGate
from silvirica.graph.graph_db import GraphDatabase
from silvirica.graph.query import GraphQueryEngine
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.models.router import ModelRouter
from silvirica.observatory.telemetry import TelemetryStore
from silvirica.repository.symbols import SymbolIndex
from silvirica.skills.loader import SkillLoader


def execute_ask(
    arg1: Union[Path, str],
    arg2: Optional[Union[Path, str]] = None,
    show_telemetry_box: bool = True,
) -> str:
    start_time = time.time()
    if isinstance(arg1, Path):
        root_path = arg1.resolve()
        query = str(arg2 or "")
    elif isinstance(arg2, Path):
        root_path = arg2.resolve()
        query = str(arg1 or "")
    else:
        root_path = Path.cwd()
        query = str(arg1 or "")

    brain = ProjectBrain(root_path)
    if not brain.is_initialized:
        brain.init()

    config = load_config(root_path)
    telemetry_store = TelemetryStore(brain.metrics_dir / "telemetry.db")
    symbol_index = SymbolIndex(brain.symbols_dir / "symbols.db")
    graph_db = GraphDatabase(brain.graph_dir / "graph.db")
    graph_query = GraphQueryEngine(graph_db)
    vault = ObsidianMemoryVault(brain.memory_dir)
    skill_loader = SkillLoader(brain.skills_dir)
    model_router = ModelRouter(config)

    # 1. Fast Gate
    gate_decision = FastGate.evaluate(
        query=query,
        root_path=root_path,
        symbol_index=symbol_index,
        memory_vault=vault,
        graph_engine=graph_query,
    )

    # 2. Check Zero-Model Path
    if gate_decision.is_zero_model and gate_decision.zero_model_result:
        latency = time.time() - start_time
        baseline_estimate = 15000
        tokens_saved = baseline_estimate

        event = TelemetryEvent(
            query=query,
            complexity=gate_decision.complexity,
            category=RoutingCategory.LOCAL,
            model_used="zero-model-deterministic",
            input_tokens=0,
            output_tokens=len(gate_decision.zero_model_result) // 4,
            estimated_baseline_tokens=baseline_estimate,
            tokens_saved=tokens_saved,
            latency_seconds=latency,
            cache_hit=gate_decision.cache_hit,
            zero_model=True,
            skills_activated=[],
            files_retrieved=1,
            symbols_retrieved=1,
        )
        decision_details = {
            "query": query,
            "complexity": gate_decision.complexity.name,
            "intent": gate_decision.intent,
            "risk": gate_decision.risk.value,
            "zero_model": True,
            "category": "LOCAL",
            "model": "local-deterministic",
            "skills_activated": [],
            "files_retrieved": 1,
            "symbols_retrieved": 1,
            "memories_used": 0,
            "graph_nodes_used": 0,
            "cache_hit": gate_decision.cache_hit,
            "input_tokens": 0,
            "estimated_baseline": baseline_estimate,
            "reduction_percentage": 100.0,
            "latency_seconds": round(latency, 4),
            "routing_reason": "Deterministic local repository lookup satisfied query without LLM invocation.",
        }
        telemetry_store.record_event(event, decision_details)

        output = [
            "\n[SILVIRICA FAST GATE: ZERO-MODEL PATH ACTIVATED]",
            "----------------------------------------------------------------",
            gate_decision.zero_model_result,
            "----------------------------------------------------------------",
            f"Latency: {latency:.3f}s | Tokens: 0 input (100% saved) | Engine: Local Deterministic\n",
        ]
        return "\n".join(output)

    # 3. Retrieve Context
    matched_symbols = symbol_index.find_by_name(query, exact=False)[:8]
    symbol_snippets = [
        f"[{s.file_path}:{s.start_line}-{s.end_line}] {s.kind.value} {s.name} - {s.signature or ''}"
        for s in matched_symbols
    ]

    graph_context = graph_query.query_subgraph(query)
    graph_nodes = graph_context.get("nodes", [])

    memory_records = vault.search(query)[:3]
    memory_snippets = [f"Memory [[{m.title}]]: {m.content[:200]}..." for m in memory_records]

    active_skills = skill_loader.match_skills(query)
    skill_instructions = skill_loader.load_skills_level2(active_skills)

    # 4. Smart Context Compilation
    compiler = SmartContextCompiler(config)
    compiled_bundle = compiler.compile(
        task=query,
        complexity=gate_decision.complexity,
        symbols=symbol_snippets,
        memory=memory_snippets,
        graph_nodes=[n.name for n in graph_nodes],
        skills=skill_instructions,
    )

    # 5. Model Routing
    category = model_router.select_category(
        complexity=gate_decision.complexity,
        intent=gate_decision.intent,
        risk=gate_decision.risk.value,
    )
    routing_result = model_router.execute_routing(
        category=category,
        prompt=compiled_bundle.prompt,
        system_prompt=f"You are Silvirica AI Runtime Intelligence. Follow these activated skills:\n\n{compiled_bundle.skills_text}",
        max_tokens=compiled_bundle.token_budget,
    )

    latency = time.time() - start_time
    baseline_estimate = max(compiled_bundle.input_tokens * 8, 12000)
    tokens_saved = max(0, baseline_estimate - compiled_bundle.input_tokens)
    reduction_pct = round((tokens_saved / baseline_estimate) * 100, 1)

    event = TelemetryEvent(
        query=query,
        complexity=gate_decision.complexity,
        category=category,
        model_used=routing_result.get("model", "unknown"),
        input_tokens=compiled_bundle.input_tokens,
        output_tokens=routing_result.get("output_tokens", 0),
        estimated_baseline_tokens=baseline_estimate,
        tokens_saved=tokens_saved,
        latency_seconds=latency,
        cache_hit=gate_decision.cache_hit,
        zero_model=False,
        skills_activated=active_skills,
        files_retrieved=len(matched_symbols),
        symbols_retrieved=len(matched_symbols),
    )
    decision_details = {
        "query": query,
        "complexity": gate_decision.complexity.name,
        "intent": gate_decision.intent,
        "risk": gate_decision.risk.value,
        "zero_model": False,
        "category": category.value,
        "model": routing_result.get("model", "unknown"),
        "skills_activated": active_skills,
        "files_retrieved": len(matched_symbols),
        "symbols_retrieved": len(matched_symbols),
        "memories_used": len(memory_records),
        "graph_nodes_used": len(graph_nodes),
        "cache_hit": gate_decision.cache_hit,
        "input_tokens": compiled_bundle.input_tokens,
        "estimated_baseline": baseline_estimate,
        "reduction_percentage": reduction_pct,
        "latency_seconds": round(latency, 4),
        "routing_reason": f"Routed to {category.value} tier for {gate_decision.intent} task with {gate_decision.complexity.name} complexity.",
    }
    telemetry_store.record_event(event, decision_details)

    output = [
        "\n================================================================",
        f"[SILVIRICA INTELLIGENCE RESPONSE] (Tier: {category.value} | Model: {routing_result.get('model')})",
        "================================================================",
        routing_result.get("text", "No response generated."),
        "================================================================",
        f"Input Tokens: {compiled_bundle.input_tokens:,} (Baseline: ~{baseline_estimate:,} | {reduction_pct}% saved)",
        f"Latency: {latency:.3f}s | Skills: {', '.join(active_skills) or 'None'} | Symbols: {len(matched_symbols)}\n",
    ]
    return "\n".join(output)
