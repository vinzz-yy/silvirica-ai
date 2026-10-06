from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from silvirica.observatory.telemetry import TelemetryStore


class DecisionExplainer:
    """
    Renders human-readable explanation of why Silvirica routed a task,
    selected skills, retrieved context, and compiled prompt tokens.
    """

    def __init__(self, telemetry_store: TelemetryStore):
        self.store = telemetry_store

    def explain_last(self) -> str:
        decision = self.store.get_last_decision()
        if not decision:
            return "No previous decisions recorded yet. Run a query using 'silvirica ask' first."

        provider_called = decision.get("provider_called", False)
        actual_model = decision.get("actual_model", "NONE" if not provider_called else decision.get("model", "unknown"))
        selected_model = decision.get("selected_model", decision.get("model", "N/A"))
        selected_tier = decision.get("selected_tier", decision.get("category", "N/A"))

        out = []
        out.append("================================================================")
        out.append("             SILVIRICA DECISION EXPLANATION                     ")
        out.append("================================================================")
        out.append(f"Task:               {decision.get('query', 'N/A')}")
        out.append(f"Complexity:         {decision.get('complexity', 'N/A')}")
        out.append(f"Intent:             {decision.get('intent', 'N/A')}")
        out.append(f"Risk Tier:          {decision.get('risk', 'SAFE')}")
        out.append(f"Zero-Model Hit:     {'YES (Deterministic Local Engine)' if decision.get('zero_model') else 'NO'}")
        out.append(f"Selected Tier:      {selected_tier}")
        out.append(f"Selected Model:     {selected_model}")
        out.append(f"Provider Called:    {'YES' if provider_called else 'NO'}")
        out.append(f"Actual Model:       {actual_model}")
        out.append(f"Fallback Used:      {'YES' if decision.get('fallback_used') else 'NO'}")
        out.append(f"Skills Activated:   {', '.join(decision.get('skills_activated', [])) or 'None'}")
        out.append(f"Files Retrieved:    {decision.get('files_retrieved', 0)}")
        out.append(f"Symbols Retrieved:  {decision.get('symbols_retrieved', 0)}")
        out.append(f"Memory Records:     {decision.get('memories_used', 0)}")
        out.append(f"Graph Nodes:        {decision.get('graph_nodes_used', 0)}")
        out.append(f"Cache Status:       {'HIT' if decision.get('cache_hit') else 'MISS'}")
        out.append(f"Compiled Context:   {decision.get('input_tokens', 0)} tokens")
        out.append(f"Baseline Tokens:    {decision.get('estimated_baseline', 0)} tokens")
        out.append(f"Context Reduction:  {decision.get('context_reduction_percentage', decision.get('reduction_percentage', 0.0))}%")
        out.append(f"Execution Latency:  {decision.get('latency_seconds', 0.0)}s")
        out.append("----------------------------------------------------------------")
        out.append("Why this route was selected:")
        out.append(f"  {decision.get('routing_reason', 'Standard optimal path for classified complexity.')}")
        out.append("================================================================")
        return "\n".join(out)


def explain_last(root_path: Path) -> str:
    from silvirica.core.project import ProjectBrain
    brain = ProjectBrain(root_path)
    store = TelemetryStore(brain.metrics_dir / "telemetry.db")
    return DecisionExplainer(store).explain_last()

