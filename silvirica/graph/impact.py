from __future__ import annotations
from typing import Any, Dict, List, Set
from silvirica.graph.graph_db import GraphDatabase
from silvirica.core.types import NodeKind


class ProjectImpactAnalyzer:
    def __init__(self, db: GraphDatabase):
        self.db = db

    def analyze_impact(self, target_identifier: str, max_depth: int = 3) -> Dict[str, Any]:
        matching_nodes = self.db.search_nodes(target_identifier, limit=5)
        if not matching_nodes:
            return {
                "target": target_identifier, "found": False,
                "affected_files": [], "affected_symbols": [],
                "affected_routes": [], "affected_tests": [], "total_affected_nodes": 0,
            }

        affected_files: Set[str] = set()
        affected_symbols: Set[str] = set()
        affected_routes: Set[str] = set()
        affected_tests: Set[str] = set()
        visited_nodes: Set[str] = set()

        for node in matching_nodes:
            self._collect_dependents(node.id, visited_nodes, affected_files, affected_symbols, affected_routes, affected_tests, 0, max_depth)

        return {
            "target": target_identifier, "found": True,
            "affected_files": sorted(list(affected_files)),
            "affected_symbols": sorted(list(affected_symbols)),
            "affected_routes": sorted(list(affected_routes)),
            "affected_tests": sorted(list(affected_tests)),
            "total_affected_nodes": len(visited_nodes),
        }

    def _collect_dependents(self, node_id: str, visited: Set[str], affected_files: Set[str], affected_symbols: Set[str], affected_routes: Set[str], affected_tests: Set[str], current_depth: int, max_depth: int) -> None:
        if current_depth > max_depth or node_id in visited:
            return
        visited.add(node_id)
        inward = self.db.get_inward_edges(node_id)
        for edge, source_node in inward:
            if source_node.file_path:
                affected_files.add(source_node.file_path)
            if source_node.kind in [NodeKind.FUNCTION, NodeKind.CLASS, NodeKind.CONTROLLER, NodeKind.SERVICE]:
                affected_symbols.add(source_node.name)
            elif source_node.kind == NodeKind.ROUTE:
                affected_routes.add(source_node.name)
            elif source_node.kind == NodeKind.TEST:
                affected_tests.add(source_node.name)
            self._collect_dependents(source_node.id, visited, affected_files, affected_symbols, affected_routes, affected_tests, current_depth + 1, max_depth)


# Compatibility alias
ImpactAnalyzer = ProjectImpactAnalyzer
