from __future__ import annotations
import fnmatch
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from silvirica.cache.engine import CacheTier, MultiTierCacheManager
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import NodeKind, RelationKind, SymbolKind
from silvirica.graph.graph_db import GraphDatabase
from silvirica.graph.nodes import GraphNode
from silvirica.graph.relations import GraphEdge
from silvirica.repository.ast_parser import MultiLanguageASTParser
from silvirica.repository.file_hash import compute_file_hash
from silvirica.repository.symbols import SymbolIndex
from silvirica.security.sandbox import PathSandbox


class RepositoryIndexer:
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        ".php", ".phtml", ".sql", ".go", ".rs", ".java", ".kt",
        ".rb", ".c", ".cpp", ".h", ".hpp", ".cs", ".vue", ".html", ".css"
    }

    def __init__(
        self,
        root_path: Path,
        symbol_index: Optional[SymbolIndex] = None,
        graph_db: Optional[GraphDatabase] = None,
        config: Optional[ProjectConfig] = None,
        cache_manager: Optional[MultiTierCacheManager] = None,
    ):
        self.root_path = root_path.resolve()
        self.silvirica_dir = self.root_path / ".silvirica"
        self.hashes_file = self.silvirica_dir / "index" / "file_hashes.json"
        self.symbol_index = symbol_index or SymbolIndex(self.silvirica_dir / "symbols" / "symbols.db")
        self.graph_db = graph_db or GraphDatabase(self.silvirica_dir / "graph" / "graph.db")
        self.config = config or load_config(self.root_path)
        self.cache = cache_manager or MultiTierCacheManager(self.silvirica_dir / "cache")

    def _should_ignore(self, path: Path) -> bool:
        try:
            rel = str(path.relative_to(self.root_path)).replace("\\", "/")
            parts = rel.split("/")
            if len(parts) > PathSandbox.MAX_DIRECTORY_DEPTH:
                return True
        except ValueError:
            return True

        for pattern in self.config.ignore_patterns:
            pattern = pattern.replace("\\", "/")
            if any(fnmatch.fnmatch(part, pattern) for part in parts):
                return True
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f"/{rel}", pattern):
                return True
        return False

    def _load_previous_hashes(self) -> Dict[str, str]:
        if not self.hashes_file.exists():
            return {}
        try:
            with open(self.hashes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_hashes(self, hashes: Dict[str, str]) -> None:
        self.hashes_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.hashes_file, "w", encoding="utf-8") as f:
            json.dump(hashes, f, indent=2)

    def compute_project_state_hash(self, file_hashes: Dict[str, str]) -> str:
        hasher = hashlib.sha256()
        for k in sorted(file_hashes.keys()):
            hasher.update(f"{k}:{file_hashes[k]}".encode("utf-8"))
        return hasher.hexdigest()[:16]

    def index(self, force: bool = False) -> Dict[str, Any]:
        start_time = time.time()
        prev_hashes = {} if force else self._load_previous_hashes()
        new_hashes: Dict[str, str] = {}
        files_to_process: List[Path] = []
        all_files_count = 0

        for item in self.root_path.rglob("*"):
            if item.is_file():
                if self._should_ignore(item):
                    continue
                if not PathSandbox.check_file_size_limit(item):
                    continue
                if PathSandbox.is_binary_file(item):
                    continue

                all_files_count += 1
                if item.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    try:
                        rel_path = str(item.relative_to(self.root_path)).replace("\\", "/")
                    except ValueError:
                        continue
                    curr_hash = compute_file_hash(item)
                    new_hashes[rel_path] = curr_hash
                    if force or prev_hashes.get(rel_path) != curr_hash:
                        files_to_process.append(item)

        state_hash = self.compute_project_state_hash(new_hashes)

        symbols_indexed = 0
        nodes_created = 0
        edges_created = 0

        project_node_id = f"project:{self.root_path.name}"
        self.graph_db.add_node(GraphNode(id=project_node_id, kind=NodeKind.PROJECT, name=self.root_path.name, file_path=""))

        # Map symbol name to its node ID for cross-linking relations
        symbol_name_to_id: Dict[str, str] = {}

        for file_path in files_to_process:
            try:
                rel_path = str(file_path.relative_to(self.root_path)).replace("\\", "/")
            except ValueError:
                continue
            file_node_id = f"file:{rel_path}"
            file_hash = new_hashes.get(rel_path, "")

            self.graph_db.add_node(GraphNode(id=file_node_id, kind=NodeKind.FILE, name=file_path.name, file_path=rel_path))
            self.graph_db.add_edge(GraphEdge(source_id=file_node_id, target_id=project_node_id, relation=RelationKind.BELONGS_TO))

            # Check L3 AST cache
            cache_key = MultiTierCacheManager.generate_key(CacheTier.L3_AST, rel_path, file_hash)
            cached_ast = self.cache.get(CacheTier.L3_AST, cache_key)

            if cached_ast and not force:
                symbols, relations = MultiLanguageASTParser.parse_file_with_relations(file_path, self.root_path)
            else:
                symbols, relations = MultiLanguageASTParser.parse_file_with_relations(file_path, self.root_path)
                self.cache.set(
                    CacheTier.L3_AST,
                    cache_key,
                    {"symbols_count": len(symbols), "relations_count": len(relations)},
                    project_state_hash=state_hash,
                )

            self.symbol_index.save_symbols(rel_path, symbols, file_hash)
            symbols_indexed += len(symbols)

            for sym in symbols:
                sym_node_id = f"sym:{rel_path}:{sym.name}"
                symbol_name_to_id[sym.name] = sym_node_id
                node_kind = self._map_symbol_to_node_kind(sym.kind)
                self.graph_db.add_node(
                    GraphNode(
                        id=sym_node_id,
                        kind=node_kind,
                        name=sym.name,
                        file_path=rel_path,
                        line_number=sym.start_line,
                        properties={"signature": sym.signature, "docstring": sym.docstring},
                    )
                )
                nodes_created += 1
                self.graph_db.add_edge(
                    GraphEdge(source_id=sym_node_id, target_id=file_node_id, relation=RelationKind.BELONGS_TO)
                )
                edges_created += 1

            for rel in relations:
                target_node_id = symbol_name_to_id.get(rel.target_name, f"named:{rel.target_name}")
                self.graph_db.add_edge(
                    GraphEdge(
                        source_id=rel.source_identifier,
                        target_id=target_node_id,
                        relation=rel.relation,
                        properties=rel.properties,
                    )
                )
                edges_created += 1

        self._save_hashes(new_hashes)
        duration = time.time() - start_time

        return {
            "total_files_scanned": all_files_count,
            "code_files_indexed": len(new_hashes),
            "files_reindexed": len(files_to_process),
            "symbols_indexed": self.symbol_index.count(),
            "graph_nodes": self.graph_db.count_nodes(),
            "graph_edges": self.graph_db.count_edges(),
            "project_state_hash": state_hash,
            "duration_seconds": round(duration, 4),
            "incremental": not force,
        }

    def _map_symbol_to_node_kind(self, sym_kind: SymbolKind) -> NodeKind:
        mapping = {
            SymbolKind.FUNCTION: NodeKind.FUNCTION,
            SymbolKind.METHOD: NodeKind.FUNCTION,
            SymbolKind.CLASS: NodeKind.CLASS,
            SymbolKind.ROUTE: NodeKind.ROUTE,
            SymbolKind.CONTROLLER: NodeKind.CONTROLLER,
            SymbolKind.SERVICE: NodeKind.SERVICE,
            SymbolKind.MODEL: NodeKind.MODEL,
            SymbolKind.COMPONENT: NodeKind.COMPONENT,
            SymbolKind.SCHEMA: NodeKind.TABLE,
            SymbolKind.DATABASE_TABLE: NodeKind.TABLE,
            SymbolKind.IMPORT: NodeKind.MODULE,
        }
        return mapping.get(sym_kind, NodeKind.FUNCTION)
