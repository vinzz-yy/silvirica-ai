from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from silvirica.cache.engine import CacheTier, MultiTierCacheManager
from silvirica.core.project import ProjectBrain
from silvirica.core.types import RelationKind, SymbolInfo, SymbolKind
from silvirica.graph.graph_db import GraphDatabase
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.repository.git_watcher import GitWatcher
from silvirica.repository.symbols import SymbolIndex, extract_symbol_snippet


class ZeroModelResolver:
    """
    Zero-Model Deterministic Resolver.
    Resolves factual repository questions (files, symbols, functions, call graphs,
    routes, git status, memory, config) with 0 LLM tokens, 0 cost, and ultra-low (<40ms) latency.
    """

    def __init__(
        self,
        root_path: Path,
        cache_manager: Optional[MultiTierCacheManager] = None,
        symbol_index: Optional[SymbolIndex] = None,
        vault: Optional[ObsidianMemoryVault] = None,
        graph_db: Optional[GraphDatabase] = None,
    ):
        self.root_path = root_path.resolve()
        self.silvirica_dir = self.root_path / ".silvirica"
        self.symbol_index = symbol_index or SymbolIndex(self.silvirica_dir / "symbols" / "symbols.db")
        self.vault = vault or ObsidianMemoryVault(self.silvirica_dir / "memory")
        self.graph_db = graph_db or GraphDatabase(self.silvirica_dir / "graph" / "graph.db")
        self.git_watcher = GitWatcher(self.root_path)
        self.brain = ProjectBrain(self.root_path)
        self.cache = cache_manager or MultiTierCacheManager(self.silvirica_dir / "cache")

    @classmethod
    def resolve_static(
        cls,
        query: str,
        root_path: Path,
        symbol_index: Optional[SymbolIndex] = None,
        vault: Optional[ObsidianMemoryVault] = None,
        graph_db: Optional[GraphDatabase] = None,
    ) -> Optional[str]:
        instance = cls(root_path, symbol_index=symbol_index, vault=vault, graph_db=graph_db)
        is_zero, reason, answer, _ = instance._resolve_internal(query)
        return answer if is_zero else None

    @classmethod
    def try_resolve(
        cls,
        query: str,
        root_path: Optional[Path] = None,
        symbol_index: Optional[SymbolIndex] = None,
        vault: Optional[ObsidianMemoryVault] = None,
        graph_db: Optional[GraphDatabase] = None,
    ) -> Any:
        if root_path is not None:
            instance = cls(root_path, symbol_index=symbol_index, vault=vault, graph_db=graph_db)
            is_zero, reason, answer, _ = instance._resolve_internal(query)
            return answer if is_zero else None
        else:
            raise ValueError("root_path required for static invocation")

    def resolve(self, query: str) -> Tuple[bool, Optional[str], Optional[str], Dict[str, int]]:
        return self._resolve_internal(query)

    def _resolve_internal(self, query: str) -> Tuple[bool, Optional[str], Optional[str], Dict[str, int]]:
        query_clean = query.strip()
        query_lower = query_clean.lower()
        empty_stats = {"files_retrieved": 0, "symbols_retrieved": 0, "graph_nodes": 0}

        # ------------------------------------------------------------------
        # 1. Functions / Symbols in a specific file
        #    e.g. "What functions exist in app.py? List their exact names."
        #         "List all functions in app.py"
        #         "What symbols exist in app.py?"
        # ------------------------------------------------------------------
        file_symbol_patterns = [
            r"(?:what|which|list|show|find|get)\s+(?:functions|classes|methods|symbols|all\s+functions|all\s+symbols|exact\s+functions)?\s*(?:exist|are\s+there|are\s+defined|are\s+contained)?\s*(?:in|inside|for|of)\s+['\"]?([A-Za-z0-9_./\-]+\.[A-Za-z0-9]+)['\"]?",
            r"(?:functions|symbols|classes)\s+(?:in|inside|of)\s+['\"]?([A-Za-z0-9_./\-]+\.[A-Za-z0-9]+)['\"]?",
        ]
        for pat in file_symbol_patterns:
            m = re.search(pat, query_lower)
            if m:
                target_file_name = m.group(1).strip()
                # Find matching symbols in symbol index
                symbols = self.symbol_index.find_by_file(target_file_name, exact=False)
                
                # If symbols not found in DB, try on-the-fly AST parse for Python file
                if not symbols:
                    candidate_file = self.root_path / target_file_name
                    if not candidate_file.exists():
                        # Search for file
                        matches = list(self.root_path.rglob(f"*{target_file_name}"))
                        if matches:
                            candidate_file = matches[0]
                    if candidate_file.exists() and candidate_file.suffix.lower() == ".py":
                        try:
                            code = candidate_file.read_text(encoding="utf-8", errors="ignore")
                            tree = ast.parse(code)
                            rel_p = str(candidate_file.relative_to(self.root_path)).replace("\\", "/")
                            for node in tree.body:
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    symbols.append(
                                        SymbolInfo(
                                            name=node.name,
                                            kind=SymbolKind.FUNCTION,
                                            file_path=rel_p,
                                            start_line=node.lineno,
                                            end_line=getattr(node, "end_lineno", node.lineno),
                                            signature=f"def {node.name}(...)",
                                        )
                                    )
                                elif isinstance(node, ast.ClassDef):
                                    symbols.append(
                                        SymbolInfo(
                                            name=node.name,
                                            kind=SymbolKind.CLASS,
                                            file_path=rel_p,
                                            start_line=node.lineno,
                                            end_line=getattr(node, "end_lineno", node.lineno),
                                        )
                                    )
                        except Exception:
                            pass

                if symbols:
                    # Filter if specific symbol kind requested
                    if "function" in query_lower:
                        filtered = [s for s in symbols if s.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD)]
                        if not filtered:
                            filtered = symbols
                    elif "class" in query_lower:
                        filtered = [s for s in symbols if s.kind == SymbolKind.CLASS]
                        if not filtered:
                            filtered = symbols
                    else:
                        filtered = symbols

                    names_list = [s.name for s in filtered]
                    lines = [
                        f"[ZERO-MODEL] Found {len(filtered)} symbol(s) in '{target_file_name}':",
                    ]
                    for s in filtered:
                        sig_str = f" - `{s.signature}`" if s.signature else ""
                        lines.append(f"- **{s.name}** ({s.kind.value}, lines {s.start_line}-{s.end_line}){sig_str}")

                    lines.append("\nExact symbol names:")
                    for n in names_list:
                        lines.append(f"- {n}")

                    stats = {
                        "files_retrieved": 1,
                        "symbols_retrieved": len(filtered),
                        "graph_nodes": 0,
                    }
                    return True, f"File Symbol Index Lookup for '{target_file_name}' (0 LLM Tokens)", "\n".join(lines), stats

        # ------------------------------------------------------------------
        # 2. Call Graph Queries: "What functions does checkout call?" / "What does checkout call?"
        # ------------------------------------------------------------------
        call_patterns = [
            r"(?:what|which)\s+(?:functions|methods|calls)?\s*(?:does|do)?\s*['\"]?([A-Za-z0-9_]+)['\"]?\s*(?:call|invoke|use|depend on)\??$",
            r"^show\s+(?:calls|callees|dependencies)\s+(?:for|of|from)\s+['\"]?([A-Za-z0-9_]+)['\"]?\??$",
            r"^what does\s+['\"]?([A-Za-z0-9_]+)['\"]?\s+call\??$",
        ]
        for pat in call_patterns:
            m = re.match(pat, query_lower)
            if m:
                caller_name = m.group(1)
                # Search graph outward edges
                callees: List[str] = []
                matching_nodes = self.graph_db.search_nodes(caller_name)
                for node in matching_nodes:
                    if node.name == caller_name:
                        outward = self.graph_db.get_outward_edges(node.id)
                        for edge, target in outward:
                            if edge.relation in (RelationKind.CALLS, RelationKind.DEPENDS_ON, RelationKind.USES):
                                if target.name not in callees and target.name != caller_name:
                                    callees.append(target.name)

                # If no callees found in graph DB, inspect AST directly if available
                if not callees:
                    sym_matches = self.symbol_index.find_by_name(caller_name, exact=True)
                    for sym in sym_matches:
                        file_p = self.root_path / sym.file_path
                        if file_p.exists() and file_p.suffix.lower() == ".py":
                            try:
                                code = file_p.read_text(encoding="utf-8", errors="ignore")
                                tree = ast.parse(code)
                                for node in ast.walk(tree):
                                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == caller_name:
                                        for sub in ast.walk(node):
                                            if isinstance(sub, ast.Call):
                                                if isinstance(sub.func, ast.Name) and sub.func.id != caller_name:
                                                    if sub.func.id not in callees:
                                                        callees.append(sub.func.id)
                                                elif isinstance(sub.func, ast.Attribute):
                                                    if sub.func.attr not in callees:
                                                        callees.append(sub.func.attr)
                            except Exception:
                                pass

                if callees:
                    lines = [f"[ZERO-MODEL] Function '{caller_name}' calls {len(callees)} function(s):"]
                    for c in callees:
                        lines.append(f"- **{c}**")
                    lines.append("\nExact called functions:")
                    for c in callees:
                        lines.append(f"- {c}")

                    stats = {
                        "files_retrieved": 1,
                        "symbols_retrieved": len(callees) + 1,
                        "graph_nodes": len(callees) + 1,
                    }
                    return True, f"Call Graph Query for '{caller_name}' (0 LLM Tokens)", "\n".join(lines), stats

        # ------------------------------------------------------------------
        # 3. Caller Queries: "Who calls calculate_total?" / "What calls calculate_total?"
        # ------------------------------------------------------------------
        caller_patterns = [
            r"(?:who|what|which functions|which callers)\s+(?:calls|call|invokes|invoke)\s+['\"]?([A-Za-z0-9_]+)['\"]?\??$",
            r"^show\s+callers\s+(?:for|of)\s+['\"]?([A-Za-z0-9_]+)['\"]?\??$",
        ]
        for pat in caller_patterns:
            m = re.match(pat, query_lower)
            if m:
                target_name = m.group(1)
                callers: List[str] = []
                matching_nodes = self.graph_db.search_nodes(target_name)
                for node in matching_nodes:
                    if node.name == target_name:
                        inward = self.graph_db.get_inward_edges(node.id)
                        for edge, source in inward:
                            if edge.relation in (RelationKind.CALLS, RelationKind.USES):
                                if source.name not in callers and source.name != target_name:
                                    callers.append(source.name)

                if callers:
                    lines = [f"[ZERO-MODEL] Function '{target_name}' is called by {len(callers)} caller(s):"]
                    for c in callers:
                        lines.append(f"- **{c}**")
                    stats = {
                        "files_retrieved": 1,
                        "symbols_retrieved": len(callers) + 1,
                        "graph_nodes": len(callers) + 1,
                    }
                    return True, f"Inward Caller Graph Query for '{target_name}' (0 LLM Tokens)", "\n".join(lines), stats

        # ------------------------------------------------------------------
        # 4. Symbol Definition / Location Queries
        #    e.g. "Where is checkout defined?"
        #         "What file contains calculate_total?"
        #         "Where is calculate_discount defined?"
        # ------------------------------------------------------------------
        where_defined_patterns = [
            r"^(?:where is|locate|find|what file contains|which file contains|which file defines|what file defines)\s+(?:the\s+)?(?:class|function|method|symbol|controller|model|component)?\s*['\"]?([A-Za-z0-9_]+)['\"]?\s*(?:defined|located|implemented)?\??$",
            r"^where is\s+['\"]?([A-Za-z0-9_]+)['\"]?\??$",
            r"^show\s+(?:code\s+for|definition\s+of|symbol)\s+['\"]?([A-Za-z0-9_]+)['\"]?$",
            r"^what is\s+['\"]?([A-Za-z0-9_]+)['\"]?\??$",
        ]
        for pat in where_defined_patterns:
            m = re.match(pat, query_lower)
            if m:
                symbol_name = m.group(1)
                matches = self.symbol_index.find_by_name(symbol_name, exact=True)
                if not matches:
                    matches = self.symbol_index.find_by_name(symbol_name, exact=False)

                if matches:
                    lines = [f"[ZERO-MODEL] Found definition for '{symbol_name}':"]
                    files_set = set()
                    for s in matches[:5]:
                        files_set.add(s.file_path)
                        lines.append(f"- **{s.name}** ({s.kind.value}): `{s.file_path}` (lines {s.start_line}-{s.end_line})")
                        if s.signature:
                            lines.append(f"  Signature: `{s.signature}`")
                        snippet = extract_symbol_snippet(self.root_path, s)
                        if snippet:
                            lines.append("  ```")
                            lines.append(snippet[:500] + ("..." if len(snippet) > 500 else ""))
                            lines.append("  ```")

                    stats = {
                        "files_retrieved": len(files_set),
                        "symbols_retrieved": len(matches),
                        "graph_nodes": 0,
                    }
                    return True, f"Symbol Index Lookup for '{symbol_name}' (0 LLM Tokens)", "\n".join(lines), stats

        # ------------------------------------------------------------------
        # 5. File lookup: "where is file app.py"
        # ------------------------------------------------------------------
        file_patterns = [
            r"^(?:where is|find|locate|show)\s+(?:file|path)\s+['\"]?([A-Za-z0-9_./\-]+)['\"]?\??$",
        ]
        for pat in file_patterns:
            m = re.match(pat, query_lower)
            if m:
                target_file = m.group(1).strip()
                matches = list(self.root_path.rglob(f"*{target_file}*"))
                valid_matches = [
                    str(p.relative_to(self.root_path)).replace("\\", "/")
                    for p in matches
                    if not any(part.startswith(".") or part in ["node_modules", "vendor", "__pycache__", "venv", ".venv"] for part in p.parts)
                ]
                if valid_matches:
                    lines = [f"[ZERO-MODEL] Located {len(valid_matches)} file(s) matching '{target_file}':"]
                    for vm in valid_matches[:8]:
                        lines.append(f"- `{vm}`")
                    stats = {"files_retrieved": len(valid_matches), "symbols_retrieved": 0, "graph_nodes": 0}
                    return True, "Deterministic File Lookup (0 LLM Tokens)", "\n".join(lines), stats

        # ------------------------------------------------------------------
        # 6. Git status / diff
        # ------------------------------------------------------------------
        if any(term in query_lower for term in ["git diff", "git status", "show changes", "what changed", "git log"]):
            diff = self.git_watcher.get_diff_summary()
            stats = {"files_retrieved": 1, "symbols_retrieved": 0, "graph_nodes": 0}
            return True, "Local Git Status (0 LLM Tokens)", f"[ZERO-MODEL] Current Git Status:\n```\n{diff}\n```", stats

        # ------------------------------------------------------------------
        # 7. Tech stack & frameworks
        # ------------------------------------------------------------------
        if any(term in query_lower for term in ["tech stack", "what framework", "what languages", "project stack", "project metadata"]):
            info = self.brain.load_project_json()
            if info:
                langs = ", ".join(info.get("languages", [])) or "None detected"
                fws = ", ".join(info.get("frameworks", [])) or "None detected"
                answer = (
                    f"[ZERO-MODEL] Project Stack for {info.get('name', 'Project')}:\n"
                    f"- **Languages**: {langs}\n"
                    f"- **Frameworks**: {fws}\n"
                    f"- **Mode**: {info.get('mode', 'AUTO')}"
                )
                stats = {"files_retrieved": 1, "symbols_retrieved": 0, "graph_nodes": 0}
                return True, "Project Brain Metadata (0 LLM Tokens)", answer, stats

        # ------------------------------------------------------------------
        # 8. List routes / endpoints
        # ------------------------------------------------------------------
        if any(term in query_lower for term in ["list routes", "show routes", "all routes", "api routes", "endpoints"]):
            route_matches = self.symbol_index.find_by_name(" ", exact=False)
            route_symbols = [s for s in route_matches if s.kind == SymbolKind.ROUTE]
            if route_symbols:
                lines = [f"[ZERO-MODEL] Discovered {len(route_symbols)} route(s):"]
                for r in route_symbols[:15]:
                    lines.append(f"- `{r.name}` -> `{r.file_path}` (line {r.start_line})")
                stats = {"files_retrieved": len(set(r.file_path for r in route_symbols)), "symbols_retrieved": len(route_symbols), "graph_nodes": 0}
                return True, "Route Symbol Index (0 LLM Tokens)", "\n".join(lines), stats

        # ------------------------------------------------------------------
        # 9. Obsidian Memory exact match
        # ------------------------------------------------------------------
        memories = self.vault.search(query_clean)
        if memories and len(query_clean.split()) <= 5:
            for m in memories:
                if m.title.lower() == query_lower or query_lower in m.title.lower():
                    stats = {"files_retrieved": 1, "symbols_retrieved": 0, "graph_nodes": 0}
                    return True, "Obsidian Memory Match (0 LLM Tokens)", f"[ZERO-MODEL] Memory [[{m.title}]]:\n\n{m.content}", stats

        return False, None, None, empty_stats

