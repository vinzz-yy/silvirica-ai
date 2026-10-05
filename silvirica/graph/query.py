from __future__ import annotations
from typing import Any, Dict, List, Set
from silvirica.graph.graph_db import GraphDatabase


class GraphQueryEngine:
    def __init__(self, db: GraphDatabase):
        self.db = db

    def query(self, search_term: str, depth: int = 2) -> str:
        matching_nodes = self.db.search_nodes(search_term, limit=10)
        if not matching_nodes:
            return f"No graph nodes found matching '{search_term}'."

        output_lines = [f"=== Graph Intelligence for '{search_term}' ==="]
        visited_edges: Set[str] = set()

        for start_node in matching_nodes:
            output_lines.append(f"\nRoot: [{start_node.kind.value}] {start_node.name} ({start_node.id})")
            self._format_traversal(start_node.id, output_lines, visited_edges, current_depth=0, max_depth=depth)

        return "\n".join(output_lines)

    def query_subgraph(self, search_term: str, depth: int = 2) -> Dict[str, Any]:
        matching_nodes = self.db.search_nodes(search_term, limit=10)
        formatted = self.query(search_term, depth)
        return {
            "nodes": [
                {
                    "id": n.id,
                    "kind": n.kind.value if hasattr(n.kind, "value") else str(n.kind),
                    "name": n.name,
                    "file_path": n.file_path,
                    "line_number": n.line_number,
                    "properties": n.properties,
                }
                for n in matching_nodes
            ],
            "count": len(matching_nodes),
            "formatted": formatted,
        }

    def _format_traversal(self, node_id: str, output_lines: List[str], visited_edges: Set[str], current_depth: int, max_depth: int) -> None:
        if current_depth >= max_depth:
            return
        outward = self.db.get_outward_edges(node_id)
        indent = "  " * (current_depth + 1)
        for edge, target in outward:
            edge_key = f"{edge.source_id}->{edge.relation.value}->{edge.target_id}"
            if edge_key in visited_edges:
                continue
            visited_edges.add(edge_key)
            output_lines.append(f"{indent}--({edge.relation.value})--> [{target.kind.value}] {target.name}")
            self._format_traversal(target.id, output_lines, visited_edges, current_depth + 1, max_depth)
