from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from silvirica.benchmark.scenarios import BENCHMARK_SCENARIOS, BenchmarkScenario
from silvirica.context.compiler import SmartContextCompiler
from silvirica.core.config import load_config
from silvirica.core.project import ProjectBrain
from silvirica.fastgate.gate import FastGate
from silvirica.graph.graph_db import GraphDatabase
from silvirica.graph.query import GraphQueryEngine
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.models.router import ModelRouter
from silvirica.repository.symbols import SymbolIndex
from silvirica.skills.loader import SkillLoader


class BenchmarkHarness:
    """
    Automated benchmark harness comparing:
    - WITHOUT SILVIRICA (Naïve whole repo / unranked context)
    - WITH SILVIRICA (FastGate + Smart Context Compiler + Zero-Model + Progressive Skills)
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.brain = ProjectBrain(self.root_path)
        if not self.brain.is_initialized:
            self.brain.init()
        self.config = load_config(self.root_path)
        self.symbol_index = SymbolIndex(self.brain.symbols_dir / "symbols.db")
        self.graph_db = GraphDatabase(self.brain.graph_dir / "graph.db")
        self.graph_query = GraphQueryEngine(self.graph_db)
        self.vault = ObsidianMemoryVault(self.brain.memory_dir)
        self.skill_loader = SkillLoader(self.brain.skills_dir)
        self.model_router = ModelRouter(self.config)
        self.compiler = SmartContextCompiler(self.config)

    def run_all(self, scenarios: Optional[List[BenchmarkScenario]] = None) -> List[Dict[str, Any]]:
        target_scenarios = scenarios or BENCHMARK_SCENARIOS
        results = []

        for sc in target_scenarios:
            res = self.run_scenario(sc)
            results.append(res)

        return results

    def run_scenario(self, scenario: BenchmarkScenario) -> Dict[str, Any]:
        # 1. Baseline simulation (Naïve context reading whole files)
        naive_tokens = scenario.naive_estimated_tokens
        naive_files = max(len(scenario.target_files) * 6, 12)
        naive_latency = round(0.5 + (naive_tokens / 10000.0) * 1.5, 3)

        # 2. Silvirica optimized pipeline
        start_time = time.time()
        gate_decision = FastGate.evaluate(
            query=scenario.task,
            root_path=self.root_path,
            symbol_index=self.symbol_index,
            memory_vault=self.vault,
            graph_engine=self.graph_query,
        )

        silvirica_input_tokens = 0
        silvirica_files = 0
        zero_model = False
        active_skills = []

        if gate_decision.is_zero_model:
            zero_model = True
            silvirica_input_tokens = 0
            silvirica_files = 1
        else:
            symbols = self.symbol_index.find_by_name(scenario.task)[:4]
            symbol_snippets = [f"[{s.file_path}:{s.start_line}] {s.name}" for s in symbols]
            silvirica_files = len(set(s.file_path for s in symbols)) or 1

            active_skills = self.skill_loader.match_skills(scenario.task)
            skill_text = self.skill_loader.load_skills_level2(active_skills)

            compiled = self.compiler.compile(
                task=scenario.task,
                complexity=gate_decision.complexity,
                symbols=symbol_snippets,
                skills=skill_text,
            )
            silvirica_input_tokens = compiled.input_tokens

        latency = round(time.time() - start_time, 4)
        tokens_saved = naive_tokens - silvirica_input_tokens
        reduction_pct = round((tokens_saved / naive_tokens) * 100, 1)

        return {
            "id": scenario.id,
            "title": scenario.title,
            "task": scenario.task,
            "expected_complexity": scenario.expected_complexity.name,
            "naive": {
                "input_tokens": naive_tokens,
                "files_inspected": naive_files,
                "latency_seconds": naive_latency,
                "model_calls": 1,
            },
            "silvirica": {
                "input_tokens": silvirica_input_tokens,
                "files_inspected": silvirica_files,
                "latency_seconds": latency,
                "zero_model": zero_model,
                "skills_activated": active_skills,
                "model_calls": 0 if zero_model else 1,
            },
            "tokens_saved": tokens_saved,
            "reduction_percentage": reduction_pct,
            "latency_improvement_percentage": round(max(0.0, (naive_latency - latency) / naive_latency) * 100, 1),
        }
