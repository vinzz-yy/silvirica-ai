"""
Silvirica AI Status Command.
"""

from __future__ import annotations
from pathlib import Path
from silvirica.core.project import ProjectBrain
from silvirica.graph.graph_db import GraphDatabase
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.observatory.metrics import MetricsCalculator
from silvirica.observatory.telemetry import TelemetryStore
from silvirica.repository.symbols import SymbolIndex
from silvirica.skills.loader import SkillLoader


def show_status(root_path: Path) -> None:
    root = root_path.resolve()
    silvirica_dir = root / ".silvirica"
    brain = ProjectBrain(root)

    if not brain.is_initialized:
        print(f"Silvirica is not initialized in {root}. Run 'silvirica init' to begin.")
        return

    proj = brain.load_project_json()
    cfg = brain.get_config()
    sym_idx = SymbolIndex(silvirica_dir / "symbols" / "symbols.db")
    graph = GraphDatabase(silvirica_dir / "graph" / "graph.db")
    vault = ObsidianMemoryVault(silvirica_dir / "memory")
    loader = SkillLoader(silvirica_dir / "skills")
    telemetry = TelemetryStore(silvirica_dir / "metrics" / "telemetry.db")
    metrics = MetricsCalculator(telemetry).calculate_summary()

    print("====================== SILVIRICA STATUS ======================")
    print(f"Version:           0.1.0")
    print(f"Project:           {proj.get('name', root.name)}")
    print(f"Operating Mode:    {cfg.mode}")
    print(f"Languages:         {', '.join(proj.get('languages', [])) or 'None'}")
    print(f"Frameworks:        {', '.join(proj.get('frameworks', [])) or 'None'}")
    print("--------------------------------------------------------------")
    print(f"Symbols Indexed:   {sym_idx.count():,}")
    print(f"Graph Nodes:       {graph.count_nodes():,}")
    print(f"Graph Edges:       {graph.count_edges():,}")
    print(f"Memory Notes:      {len(vault.list_notes())}")
    print(f"Installed Skills:  {len(loader.list_skills())}")
    print(f"Active Skills:     {', '.join(cfg.active_skills)}")
    print("--------------------------------------------------------------")
    print(f"Silvirica Score:   {metrics['silvirica_score']}/100")
    print(f"Token Savings:     {metrics['tokens_saved_percent']:.1f}%")
    print(f"Average Latency:   {metrics['avg_latency']:.2f} sec")
    print(f"Zero-Model Tasks:  {metrics['zero_model_count']}")
    print(f"Cache Hit Rate:    {metrics['cache_hit_rate']:.1f}%")
    print("==============================================================")
