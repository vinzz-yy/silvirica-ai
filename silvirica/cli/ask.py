from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from silvirica.cache.engine import MultiTierCacheManager
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
from silvirica.repository.git_watcher import GitWatcher
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
    cache_manager = MultiTierCacheManager(brain.cache_dir)
    telemetry_store = TelemetryStore(brain.metrics_dir / "telemetry.db")
    symbol_index = SymbolIndex(brain.symbols_dir / "symbols.db")
    graph_db = GraphDatabase(brain.graph_dir / "graph.db")
    graph_query = GraphQueryEngine(graph_db)
    vault = ObsidianMemoryVault(brain.memory_dir)
    skill_loader = SkillLoader(brain.skills_dir)
    model_router = ModelRouter(config, cache_manager=cache_manager)
    git_watcher = GitWatcher(root_path)

    # Load state hash
    hashes_file = brain.index_dir / "file_hashes.json"
    state_hash = ""
    if hashes_file.exists():
        try:
            with open(hashes_file, "r", encoding="utf-8") as f:
                hashes = json.load(f)
            import hashlib
            hasher = hashlib.sha256()
            for k in sorted(hashes.keys()):
                hasher.update(f"{k}:{hashes[k]}".encode("utf-8"))
            state_hash = hasher.hexdigest()[:16]
        except Exception:
            state_hash = ""

    # 1. Fast Gate Check
    gate_decision = FastGate.evaluate(
        query=query,
        root_path=root_path,
        symbol_index=symbol_index,
        memory_vault=vault,
        graph_engine=graph_query,
        cache_manager=cache_manager,
        state_hash=state_hash,
    )

    # 2. Check Zero-Model Path / L1 Cache
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
            "routing_reason": gate_decision.zero_model_reason or "Deterministic local repository lookup satisfied query without LLM invocation.",
        }
        telemetry_store.record_event(event, decision_details)

        cache_label = " [L1 CACHE HIT]" if gate_decision.cache_hit else ""
        output = [
            f"\n[SILVIRICA FAST GATE: ZERO-MODEL PATH ACTIVATED{cache_label}]",
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

    # Gather dependency & caller graph edges
    direct_dependencies: List[str] = []
    callers_callees: List[str] = []
    for s in matched_symbols[:3]:
        sym_node_id = f"sym:{s.file_path}:{s.name}"
        outward = graph_db.get_outward_edges(sym_node_id)
        for edge, target in outward:
            direct_dependencies.append(f"{s.name} --({edge.relation.value})--> {target.name} ({target.kind.value})")

        inward = graph_db.get_inward_edges(sym_node_id)
        for edge, source in inward:
            callers_callees.append(f"{source.name} ({source.kind.value}) --({edge.relation.value})--> {s.name}")

    graph_context = graph_query.query_subgraph(query)
    graph_nodes = graph_context.get("nodes", [])

    memory_records = vault.search(query, limit=3)
    memory_snippets = [f"Memory [[{m.title}]]: {m.content[:250]}..." for m in memory_records]

    # Git diffs if relevant
    is_bug_task = any(t in query.lower() for t in ["bug", "error", "fail", "broken", "fix", "issue", "why"])
    git_diff_summary = git_watcher.get_diff_summary() if is_bug_task else None

    # JEV Decision & Fast Intelligence Layer (TypeSafe System One)
    jev_decision = None
    if getattr(config, "jev", None) and config.jev.enabled:
        try:
            from silvirica.capabilities.jev import JEVCapability
            jev_cap = JEVCapability.get_instance(config=config.jev, project_config=config)
            jev_decision = jev_cap.route(query, state_hash=state_hash)
            if config.jev.skill_routing and jev_decision.skills:
                available_skill_names = [sk.name for sk in skill_loader.list_skills()]
                matched_jev_skills = [s for s in jev_decision.skills if s in available_skill_names]
                active_skills = matched_jev_skills if matched_jev_skills else skill_loader.match_skills(query, max_skills=2)
            else:
                active_skills = skill_loader.match_skills(query, max_skills=3)
        except Exception:
            active_skills = skill_loader.match_skills(query, max_skills=3)
    else:
        active_skills = skill_loader.match_skills(query, max_skills=3)

    skill_instructions = skill_loader.load_skills_level2(active_skills)

    # 4. Smart Context Compilation
    compiler = SmartContextCompiler(config, cache_manager=cache_manager)
    compiled_bundle = compiler.compile(
        task=query,
        complexity=gate_decision.complexity,
        symbols=symbol_snippets,
        dependencies=direct_dependencies[:5],
        callers_callees=callers_callees[:5],
        memory=memory_snippets,
        graph_nodes=[(n.get("name", "") if isinstance(n, dict) else n.name) for n in graph_nodes],
        skills=skill_instructions,
        git_diffs=git_diff_summary,
        state_hash=state_hash,
    )

    # Apply JEV context token budgeting if active
    effective_token_budget = compiled_bundle.token_budget
    if jev_decision and config.jev.context_routing and jev_decision.context_budget > 0:
        effective_token_budget = min(compiled_bundle.token_budget, jev_decision.context_budget)

    # 5. Model Routing & Execution
    category = model_router.select_category(
        complexity=gate_decision.complexity,
        intent=gate_decision.intent,
        risk=gate_decision.risk.value,
    )
    routing_result = model_router.execute_routing(
        category=category,
        prompt=compiled_bundle.prompt,
        system_prompt=f"You are Silvirica AI Runtime Intelligence. Follow these activated skills:\n\n{compiled_bundle.skills_text}",
        max_tokens=effective_token_budget,
        task=query,
        state_hash=state_hash,
    )

    latency = time.time() - start_time
    baseline_estimate = compiled_bundle.naive_baseline_tokens
    tokens_saved = max(0, baseline_estimate - compiled_bundle.input_tokens)
    reduction_pct = compiled_bundle.reduction_percentage

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
        cache_hit=routing_result.get("cache_hit", False) or compiled_bundle.cache_hit,
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
        "cache_hit": routing_result.get("cache_hit", False),
        "input_tokens": compiled_bundle.input_tokens,
        "estimated_baseline": baseline_estimate,
        "reduction_percentage": reduction_pct,
        "latency_seconds": round(latency, 4),
        "routing_reason": f"Routed to {category.value} tier for {gate_decision.intent} task with {gate_decision.complexity.name} complexity.",
    }
    telemetry_store.record_event(event, decision_details)

    cache_badge = " [L7 CACHE HIT]" if routing_result.get("cache_hit") else ""
    output = [
        "\n================================================================",
        f"[SILVIRICA INTELLIGENCE RESPONSE{cache_badge}] (Tier: {category.value} | Model: {routing_result.get('model')})",
        "================================================================",
        routing_result.get("text", "No response generated."),
        "================================================================",
        f"Input Tokens: {compiled_bundle.input_tokens:,} (Baseline: ~{baseline_estimate:,} | {reduction_pct}% saved)",
        f"Latency: {latency:.3f}s | Skills Active: {', '.join(active_skills) or 'None'}",
        "================================================================\n",
    ]
    return "\n".join(output)
