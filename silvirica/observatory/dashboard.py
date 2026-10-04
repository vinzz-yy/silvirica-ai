from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.project import ProjectBrain
from silvirica.observatory.metrics import ImprovementScoreCalculator
from silvirica.observatory.telemetry import TelemetryStore


class ObservatoryDashboard:
    """
    Renders the Silvirica Observatory terminal dashboard.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.brain = ProjectBrain(self.root_path)
        self.config = load_config(self.root_path)
        self.telemetry = TelemetryStore(self.brain.metrics_dir / "telemetry.db")

    def render(self) -> str:
        summary = self.telemetry.get_summary()
        score_data = ImprovementScoreCalculator.calculate_score(summary)
        score = score_data["overall_score"]

        # Gather repository facts
        project_json = self.brain.load_project_json()
        name = project_json.get("name", self.root_path.name)
        languages = ", ".join(self.config.languages) or "Multi"
        frameworks = ", ".join(self.config.frameworks) or "Standard"

        # Count symbols and graph nodes
        symbols_count = 0
        symbols_db_path = self.brain.symbols_dir / "symbols.db"
        if symbols_db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(symbols_db_path))
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM symbols")
                symbols_count = cur.fetchone()[0]
                conn.close()
            except Exception:
                symbols_count = 0

        graph_nodes_count = 0
        graph_db_path = self.brain.graph_dir / "graph.db"
        if graph_db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(graph_db_path))
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM nodes")
                graph_nodes_count = cur.fetchone()[0]
                conn.close()
            except Exception:
                graph_nodes_count = 0

        # Memory notes count
        mem_notes_count = len(list(self.brain.memory_dir.glob("*.md")))

        out = []
        out.append("======================================================================")
        out.append("                 SILVIRICA AI OBSERVATORY DASHBOARD                  ")
        out.append("======================================================================")
        out.append(f"Project:              {name}")
        out.append(f"Tech Stack:           Languages: {languages} | Frameworks: {frameworks}")
        out.append(f"Operating Mode:       {self.config.mode}")
        out.append(f"Silvirica Score:      {score}/100")
        out.append("----------------------------------------------------------------------")
        out.append("PERFORMANCE & EFFICIENCY TELEMETRY:")
        out.append(f"  - Total Queries Tracked:     {summary['total_queries']}")
        out.append(f"  - Tokens Saved:              {summary['total_tokens_saved']:,} ({summary['savings_percentage']}%)")
        out.append(f"  - Average Latency:           {summary['avg_latency']}s")
        out.append(f"  - Cache Hit Rate:            {summary['cache_hit_rate']}%")
        out.append(f"  - Zero-Model Path Rate:      {summary['zero_model_rate']}%")
        out.append("----------------------------------------------------------------------")
        out.append("PROJECT BRAIN ASSETS:")
        out.append(f"  - Indexed Symbols:           {symbols_count:,}")
        out.append(f"  - Knowledge Graph Nodes:     {graph_nodes_count:,}")
        out.append(f"  - Memory Records:            {mem_notes_count}")
        out.append(f"  - Active Skills:             {len(self.config.active_skills)} ({', '.join(self.config.active_skills)})")
        out.append("----------------------------------------------------------------------")
        out.append("INTELLIGENCE COMPONENTS SCORE BREAKDOWN:")
        for comp, val in score_data["components"].items():
            comp_title = comp.replace("_", " ").title()
            out.append(f"  - {comp_title:26}: {val}")
        out.append("======================================================================")

        return "\n".join(out)
