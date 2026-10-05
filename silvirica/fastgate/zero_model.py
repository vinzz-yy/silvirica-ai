from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from silvirica.cache.engine import CacheTier, MultiTierCacheManager
from silvirica.core.project import ProjectBrain
from silvirica.core.types import SymbolKind
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.repository.git_watcher import GitWatcher
from silvirica.repository.symbols import SymbolIndex, extract_symbol_snippet


class ZeroModelResolver:
    """
    Zero-Model Deterministic Resolver.
    Resolves factual repository questions (files, symbols, routes, git status, memory, config)
    with 0 LLM tokens, 0 cost, and ultra-low (<40ms) latency.
    """

    def __init__(self, root_path: Path, cache_manager: Optional[MultiTierCacheManager] = None):
        self.root_path = root_path.resolve()
        self.silvirica_dir = self.root_path / ".silvirica"
        self.symbol_index = SymbolIndex(self.silvirica_dir / "symbols" / "symbols.db")
        self.vault = ObsidianMemoryVault(self.silvirica_dir / "memory")
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
    ) -> Optional[str]:
        instance = cls(root_path)
        if symbol_index:
            instance.symbol_index = symbol_index
        if vault:
            instance.vault = vault
        is_zero, reason, answer = instance._resolve_internal(query)
        return answer if is_zero else None

    @classmethod
    def try_resolve(
        cls,
        query: str,
        root_path: Optional[Path] = None,
        symbol_index: Optional[SymbolIndex] = None,
        vault: Optional[ObsidianMemoryVault] = None,
    ) -> Any:
        if root_path is not None:
            instance = cls(root_path)
            if symbol_index:
                instance.symbol_index = symbol_index
            if vault:
                instance.vault = vault
            is_zero, reason, answer = instance._resolve_internal(query)
            return answer if is_zero else None
        else:
            raise ValueError("root_path required for static invocation")

    def _resolve_internal(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        query_clean = query.strip()
        query_lower = query_clean.lower()

        # 1. Symbol queries
        symbol_patterns = [
            r"^(?:where is|find|locate)\s+(?:class|function|method|symbol|controller|model|component)?\s*['\"]?([A-Za-z0-9_]+)['\"]?\??$",
            r"^show\s+(?:code\s+for|symbol)\s+['\"]?([A-Za-z0-9_]+)['\"]?$",
            r"^what is\s+['\"]?([A-Za-z0-9_]+)['\"]?\??$",
        ]
        for pat in symbol_patterns:
            m = re.match(pat, query_lower, re.IGNORECASE)
            if m:
                symbol_name = m.group(1)
                matches = self.symbol_index.find_by_name(symbol_name, exact=False)
                if matches:
                    lines = [f"[ZERO-MODEL] Found {len(matches)} symbol match(es) for '{symbol_name}':"]
                    for s in matches[:5]:
                        lines.append(f"- **{s.name}** ({s.kind.value}): `{s.file_path}` (lines {s.start_line}-{s.end_line})")
                        if s.signature:
                            lines.append(f"  Signature: `{s.signature}`")
                        snippet = extract_symbol_snippet(self.root_path, s)
                        if snippet:
                            lines.append("  ```")
                            lines.append(snippet[:500] + ("..." if len(snippet) > 500 else ""))
                            lines.append("  ```")
                    return True, "Symbol Index Lookup (0 LLM Tokens)", "\n".join(lines)

        # 2. File lookup
        file_patterns = [
            r"^(?:where is|find|locate|show)\s+(?:file|path)\s+['\"]?([A-Za-z0-9_./\-]+)['\"]?\??$",
        ]
        for pat in file_patterns:
            m = re.match(pat, query_lower, re.IGNORECASE)
            if m:
                target_file = m.group(1).strip()
                matches = list(self.root_path.rglob(f"*{target_file}*"))
                valid_matches = [
                    str(p.relative_to(self.root_path)).replace("\\", "/")
                    for p in matches
                    if not any(part.startswith(".") or part in ["node_modules", "vendor", "__pycache__"] for part in p.parts)
                ]
                if valid_matches:
                    lines = [f"[ZERO-MODEL] Located {len(valid_matches)} file(s) matching '{target_file}':"]
                    for vm in valid_matches[:8]:
                        lines.append(f"- `{vm}`")
                    return True, "Deterministic File Lookup (0 LLM Tokens)", "\n".join(lines)

        # 3. Git status / diff
        if any(term in query_lower for term in ["git diff", "git status", "show changes", "what changed", "git log"]):
            diff = self.git_watcher.get_diff_summary()
            return True, "Local Git Status (0 LLM Tokens)", f"[ZERO-MODEL] Current Git Status:\n```\n{diff}\n```"

        # 4. Tech stack & frameworks
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
                return True, "Project Brain Metadata (0 LLM Tokens)", answer

        # 5. List routes
        if any(term in query_lower for term in ["list routes", "show routes", "all routes", "api routes", "endpoints"]):
            route_matches = self.symbol_index.find_by_name(" ", exact=False)
            route_symbols = [s for s in route_matches if s.kind == SymbolKind.ROUTE]
            if route_symbols:
                lines = [f"[ZERO-MODEL] Discovered {len(route_symbols)} route(s):"]
                for r in route_symbols[:15]:
                    lines.append(f"- `{r.name}` -> `{r.file_path}` (line {r.start_line})")
                return True, "Route Symbol Index (0 LLM Tokens)", "\n".join(lines)

        # 6. Memory exact match
        memories = self.vault.search(query_clean)
        if memories and len(query_clean.split()) <= 5:
            for m in memories:
                if m.title.lower() == query_lower or query_lower in m.title.lower():
                    return True, "Obsidian Memory Match (0 LLM Tokens)", f"[ZERO-MODEL] Memory [[{m.title}]]:\n\n{m.content}"

        return False, None, None
