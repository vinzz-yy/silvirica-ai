from __future__ import annotations
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.core.types import MemoryRecord, MemoryStatus, MemoryType
from silvirica.security.sandbox import PathSandbox


@dataclass
class StructuredMemoryEntry:
    id: str
    project: str = "default"
    type: str = "architecture"  # architecture, decisions, bugs, fixes, conventions, security, dependencies
    content: str = ""
    source: str = "agent"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_verified: float = field(default_factory=time.time)
    confidence: float = 0.95
    relevance: float = 1.0
    status: str = "active"  # active, superseded, archived
    superseded_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_to: List[str] = field(default_factory=list)


class ObsidianMemoryVault:
    """
    Obsidian-compatible Markdown Memory Vault 2.0 with Wikilinks, Tags,
    Staleness Protection, Semantic Deduplication, Path Sandboxing, and Pre-Persistence Secret Redaction.
    """

    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    TAG_PATTERN = re.compile(r'(?<!\w)#([A-Za-z0-9_-]+)')

    STANDARD_CATEGORIES = [
        "architecture", "decisions", "bugs", "fixes",
        "conventions", "security", "dependencies", "sessions", "discoveries", "glossary"
    ]

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir.resolve()
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, MemoryRecord] = {}
        self._init_standard_notes()

    def _init_standard_notes(self) -> None:
        for cat in self.STANDARD_CATEGORIES:
            cat_file = self.memory_dir / f"{cat}.md"
            if not cat_file.exists():
                cat_title = cat.replace("_", " ").title()
                cat_file.write_text(f"# {cat_title}\n\nProject memory records for {cat}.\n", encoding="utf-8")

    def _resolve_note_path(self, name: str) -> Optional[Path]:
        if not name:
            return None
        clean = re.sub(r'[\/\\:]', '_', name)
        if clean.endswith(".md"):
            clean = clean[:-3]
        clean = clean.strip(". ")
        if not clean:
            return None
        
        # Verify with PathSandbox
        try:
            target = PathSandbox.resolve_safe_path(f"{clean}.md", self.memory_dir)
            return target
        except Exception:
            return None

    def list_notes(self) -> List[str]:
        return sorted([f.stem for f in self.memory_dir.glob("*.md") if f.is_file()])

    def read_note(self, name: str) -> Optional[MemoryRecord]:
        path = self._resolve_note_path(name)
        if not path or not path.exists():
            return None

        clean_name = path.stem
        content = path.read_text(encoding="utf-8", errors="ignore")
        wikilinks = [m.group(1) for m in self.WIKILINK_PATTERN.finditer(content)]
        tags = [m.group(1) for m in self.TAG_PATTERN.finditer(content)]

        title = clean_name
        for line in content.splitlines():
            if line.strip().startswith("# "):
                title = line.strip()[2:].strip()
                break

        mem_type = MemoryType.PROJECT
        if "decision" in clean_name.lower():
            mem_type = MemoryType.DECISION
        elif "bug" in clean_name.lower() or "failure" in clean_name.lower() or "fix" in clean_name.lower():
            mem_type = MemoryType.FAILURE
        elif "session" in clean_name.lower():
            mem_type = MemoryType.SESSION

        stat = path.stat()
        record = MemoryRecord(
            id=clean_name,
            title=title,
            memory_type=mem_type,
            status=MemoryStatus.ACTIVE,
            content=content,
            tags=sorted(list(set(tags))),
            wikilinks=sorted(list(set(wikilinks))),
            created_at=stat.st_ctime,
            updated_at=stat.st_mtime,
        )
        self._cache[clean_name] = record
        return record

    def write_note(
        self,
        name: str,
        content: str,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> Optional[Path]:
        path = self._resolve_note_path(name)
        if not path:
            return None
        clean_name = path.stem
        # Pre-redact secrets before persistence
        clean_content, _ = SecretRedactor.redact(content, mode=SecurityMode.BALANCED)
        final_content = clean_content
        if tags:
            tag_line = " ".join(f"#{t.lstrip('#')}" for t in tags)
            if tag_line not in final_content:
                final_content = f"{final_content}\n\nTags: {tag_line}\n"
        path.write_text(final_content, encoding="utf-8")
        self.read_note(clean_name)
        return path

    def append_note(self, name: str, additional_content: str) -> None:
        path = self._resolve_note_path(name)
        if not path:
            return
        clean_name = path.stem
        # Pre-redact secrets before appending
        clean_add, _ = SecretRedactor.redact(additional_content, mode=SecurityMode.BALANCED)
        existing = path.read_text(encoding="utf-8") if path.exists() else f"# {clean_name}\n\n"
        
        # Deduplication check: do not append if content already exists verbatim
        if clean_add.strip() in existing:
            return

        path.write_text(f"{existing.rstrip()}\n\n{clean_add}\n", encoding="utf-8")
        self.read_note(clean_name)

    def add_structured_entry(self, entry: StructuredMemoryEntry) -> bool:
        """
        Adds a structured memory entry with deduplication, staleness protection, and secret redaction.
        """
        target_category = entry.type if entry.type in self.STANDARD_CATEGORIES else "decisions"
        cat_file = self.memory_dir / f"{target_category}.md"
        existing_text = cat_file.read_text(encoding="utf-8", errors="ignore") if cat_file.exists() else ""

        # Pre-redact secrets
        redacted_content, _ = SecretRedactor.redact(entry.content, mode=SecurityMode.BALANCED)

        # Deduplication: check lexical overlap
        entry_terms = set(re.findall(r'\w+', redacted_content.lower()))
        if entry_terms:
            existing_lines = [l.lower() for l in existing_text.splitlines() if len(l.strip()) > 10]
            for line in existing_lines:
                line_terms = set(re.findall(r'\w+', line))
                if line_terms:
                    overlap = len(entry_terms & line_terms) / len(entry_terms)
                    if overlap > 0.85:
                        return False  # Duplicate entry prevented

        # Format markdown entry
        tag_str = " ".join(f"#{t.lstrip('#')}" for t in entry.tags) if entry.tags else ""
        rel_str = ", ".join(f"[[{r}]]" for r in entry.related_to) if entry.related_to else ""

        block = f"### {entry.id}\n"
        if entry.status == "superseded" and entry.superseded_by:
            block += f"> [!WARNING] Superseded by [[{entry.superseded_by}]]\n\n"
        block += f"{redacted_content.strip()}\n"
        if rel_str:
            block += f"\n- **Related Entities**: {rel_str}\n"
        if tag_str:
            block += f"- **Tags**: {tag_str}\n"

        self.append_note(target_category, block)
        return True

    def mark_superseded(self, old_entry_id: str, new_entry_id: str) -> bool:
        for path in self.memory_dir.glob("*.md"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            if f"### {old_entry_id}" in content:
                updated = content.replace(
                    f"### {old_entry_id}\n",
                    f"### {old_entry_id}\n> [!WARNING] Superseded by [[{new_entry_id}]]\n"
                )
                path.write_text(updated, encoding="utf-8")
                self.read_note(path.stem)
                return True
        return False

    def get_memories_for_symbol(self, symbol_name: str) -> List[MemoryRecord]:
        results: List[MemoryRecord] = []
        sym_clean = symbol_name.strip().lower()
        for path in self.memory_dir.glob("*.md"):
            record = self.read_note(path.stem)
            if record:
                if sym_clean in record.content.lower() or any(sym_clean in w.lower() for w in record.wikilinks):
                    results.append(record)
        return results

    def search(self, query: str, limit: int = 10, include_superseded: bool = False) -> List[MemoryRecord]:
        results: List[Tuple[float, MemoryRecord]] = []
        query_lower = query.strip().lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]

        for path in self.memory_dir.glob("*.md"):
            record = self.read_note(path.stem)
            if not record:
                continue

            content_lower = record.content.lower()
            title_lower = record.title.lower()
            tags_lower = [t.lower() for t in record.tags]

            if not include_superseded and "superseded by" in content_lower:
                if "superseded" not in query_lower:
                    continue

            score = 0.0
            if query_lower == title_lower:
                score += 1.0
            elif query_lower in title_lower:
                score += 0.7
            elif query_lower in content_lower:
                score += 0.5

            for word in query_words:
                if word in title_lower:
                    score += 0.3
                if any(word in t for t in tags_lower):
                    score += 0.25
                if word in content_lower:
                    score += 0.1

            if score > 0:
                results.append((score, record))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def get_backlinks(self, target_note: str) -> List[str]:
        backlinks = []
        target_clean = (target_note[:-3] if target_note.endswith(".md") else target_note).lower()
        for path in self.memory_dir.glob("*.md"):
            record = self.read_note(path.stem)
            if record and path.stem.lower() != target_clean:
                if any(w.lower() == target_clean for w in record.wikilinks):
                    backlinks.append(path.stem)
        return sorted(backlinks)

    def get_vault_summary(self) -> Dict[str, Any]:
        categories_stats: Dict[str, int] = {}
        total_notes = 0

        for path in self.memory_dir.glob("*.md"):
            total_notes += 1
            content = path.read_text(encoding="utf-8", errors="ignore")
            entries = len(re.findall(r'^###\s+', content, re.MULTILINE))
            categories_stats[path.stem] = max(1, entries)

        return {
            "total_notes": total_notes,
            "categories": categories_stats,
        }

    def delete_note(self, name: str) -> bool:
        path = self._resolve_note_path(name)
        if not path or not path.exists():
            return False
        clean_name = path.stem
        path.unlink()
        if clean_name in self._cache:
            del self._cache[clean_name]
        return True

    def export_markdown_archive(self, export_path: Path) -> Path:
        safe_export = PathSandbox.resolve_safe_path(export_path, self.memory_dir.parent.parent)
        safe_export.mkdir(parents=True, exist_ok=True)
        for path in self.memory_dir.glob("*.md"):
            dest = safe_export / path.name
            dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return safe_export
