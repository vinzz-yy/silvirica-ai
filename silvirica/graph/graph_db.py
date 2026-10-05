from __future__ import annotations
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from silvirica.core.types import NodeKind, RelationKind
from silvirica.graph.nodes import GraphNode
from silvirica.graph.relations import GraphEdge


class GraphDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    file_path TEXT,
                    line_number INTEGER,
                    properties TEXT,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties TEXT,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_tgt ON edges(target_id)")

    def add_node(self, node: GraphNode) -> None:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO nodes (id, kind, name, file_path, line_number, properties, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind=excluded.kind,
                    name=excluded.name,
                    file_path=excluded.file_path,
                    line_number=excluded.line_number,
                    properties=excluded.properties,
                    updated_at=excluded.updated_at
                """,
                (
                    node.id,
                    node.kind.value if isinstance(node.kind, NodeKind) else str(node.kind),
                    node.name,
                    node.file_path,
                    node.line_number,
                    json.dumps(node.properties),
                    now,
                ),
            )

    def add_edge(self, edge: GraphEdge) -> None:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT id FROM edges WHERE source_id = ? AND target_id = ? AND relation = ?",
                (edge.source_id, edge.target_id, edge.relation.value if isinstance(edge.relation, RelationKind) else str(edge.relation)),
            )
            existing = cur.fetchone()
            if existing:
                conn.execute(
                    "UPDATE edges SET weight = ?, properties = ?, updated_at = ? WHERE id = ?",
                    (edge.weight, json.dumps(edge.properties), now, existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO edges (source_id, target_id, relation, weight, properties, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        edge.source_id,
                        edge.target_id,
                        edge.relation.value if isinstance(edge.relation, RelationKind) else str(edge.relation),
                        edge.weight,
                        json.dumps(edge.properties),
                        now,
                    ),
                )

    def search_nodes(self, query: str, limit: int = 50) -> List[GraphNode]:
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM nodes WHERE name LIKE ? OR id LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            )
            return [self._row_to_node(r) for r in cur.fetchall()]

    def get_outward_edges(self, node_id: str) -> List[Tuple[GraphEdge, GraphNode]]:
        results = []
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT e.*, n.kind as n_kind, n.name as n_name, n.file_path as n_file, n.line_number as n_line, n.properties as n_props
                FROM edges e
                JOIN nodes n ON e.target_id = n.id
                WHERE e.source_id = ?
                """,
                (node_id,),
            )
            for r in cur.fetchall():
                edge = self._row_to_edge(r)
                node = GraphNode(
                    id=r["target_id"],
                    kind=self._parse_node_kind(r["n_kind"]),
                    name=r["n_name"],
                    file_path=r["n_file"],
                    line_number=r["n_line"],
                    properties=json.loads(r["n_props"] or "{}"),
                )
                results.append((edge, node))
        return results

    def get_inward_edges(self, node_id: str) -> List[Tuple[GraphEdge, GraphNode]]:
        results = []
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT e.*, n.kind as n_kind, n.name as n_name, n.file_path as n_file, n.line_number as n_line, n.properties as n_props
                FROM edges e
                JOIN nodes n ON e.source_id = n.id
                WHERE e.target_id = ?
                """,
                (node_id,),
            )
            for r in cur.fetchall():
                edge = self._row_to_edge(r)
                node = GraphNode(
                    id=r["source_id"],
                    kind=self._parse_node_kind(r["n_kind"]),
                    name=r["n_name"],
                    file_path=r["n_file"],
                    line_number=r["n_line"],
                    properties=json.loads(r["n_props"] or "{}"),
                )
                results.append((edge, node))
        return results

    def count_nodes(self) -> int:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM nodes")
            return cur.fetchone()[0]

    def count_edges(self) -> int:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM edges")
            return cur.fetchone()[0]

    def _row_to_node(self, row: sqlite3.Row) -> GraphNode:
        return GraphNode(
            id=row["id"],
            kind=self._parse_node_kind(row["kind"]),
            name=row["name"],
            file_path=row["file_path"],
            line_number=row["line_number"],
            properties=json.loads(row["properties"] or "{}"),
        )

    def _row_to_edge(self, row: sqlite3.Row) -> GraphEdge:
        rel_str = row["relation"]
        try:
            rel = RelationKind(rel_str)
        except ValueError:
            rel = RelationKind.RELATED_TO
        return GraphEdge(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation=rel,
            weight=row["weight"],
            properties=json.loads(row["properties"] or "{}"),
        )

    def _parse_node_kind(self, kind_str: str) -> NodeKind:
        try:
            return NodeKind(kind_str)
        except ValueError:
            return NodeKind.FILE
