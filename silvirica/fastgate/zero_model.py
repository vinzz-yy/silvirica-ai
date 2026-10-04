from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Tuple
from silvirica.core.project import ProjectBrain
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.repository.git_watcher import GitWatcher
from silvirica.repository.symbols import SymbolIndex, extract_symbol_snippet


class ZeroModelResolver:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.silvirica_dir = self.root_path / ".silvirica"
        self.symbol_index = SymbolIndex(self.silvirica_dir / "symbols" / "symbols.db")
        self.vault = ObsidianMemoryVault(self.silvirica_dir / "memory")
        self.git_watcher = GitWatcher(self.root_path)
        self.brain = ProjectBrain(self.root_path)

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
        is_zero, reason, answer = instance.try_resolve(query)
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

        symbol_patterns = [
            r"^(?:where is|find|locate)\s+(?:class|function|method|symbol|controller|model)?\s*['\"]?([A-Za-z0-9_]+)['\"]?\??$",
            r"^show\s+(?:code\s+for|symbol)\s+['\"]?([A-Za-z0-9_]+)['\"]?$",
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

        if any(term in query_lower for term in ["git diff", "git status", "show changes", "what changed"]):
            diff = self.git_watcher.get_diff_summary()
            return True, "Local Git Status (0 LLM Tokens)", f"[ZERO-MODEL] Current Git Status:\n```\n{diff}\n```"

        if any(term in query_lower for term in ["tech stack", "what framework", "what languages", "project stack"]):
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

        # Check memory exact match
        memories = self.vault.search(query_clean)
        if memories and len(query_clean.split()) <= 4:
            for m in memories:
                if m.title.lower() == query_lower or query_lower in m.title.lower():
                    return True, "Obsidian Memory Match (0 LLM Tokens)", f"[ZERO-MODEL] Memory [[{m.title}]]:\n\n{m.content}"

        return False, None, None
