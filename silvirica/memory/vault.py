from __future__ import annotations
import re
from pathlib import Path
from typing import List, Optional
from silvirica.core.types import MemoryRecord, MemoryStatus, MemoryType

class ObsidianMemoryVault:
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    TAG_PATTERN = re.compile(r'(?<!\w)#([A-Za-z0-9_-]+)')

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def list_notes(self) -> List[str]:
        return [f.stem for f in self.memory_dir.glob("*.md")]

    def read_note(self, name: str) -> Optional[MemoryRecord]:
        filename = f"{name}.md" if not name.endswith(".md") else name
        path = self.memory_dir / filename
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8", errors="ignore")
        wikilinks = [m.group(1) for m in self.WIKILINK_PATTERN.finditer(content)]
        tags = [m.group(1) for m in self.TAG_PATTERN.finditer(content)]

        title = name
        for line in content.splitlines():
            if line.strip().startswith("# "):
                title = line.strip()[2:].strip()
                break

        return MemoryRecord(
            id=name, title=title, memory_type=MemoryType.PROJECT,
            status=MemoryStatus.ACTIVE, content=content,
            tags=sorted(list(set(tags))), wikilinks=sorted(list(set(wikilinks))),
        )

    def write_note(self, name: str, content: str, tags: Optional[List[str]] = None) -> Path:
        filename = f"{name}.md" if not name.endswith(".md") else name
        path = self.memory_dir / filename
        final_content = content
        if tags:
            tag_line = " ".join(f"#{t}" for t in tags)
            if tag_line not in final_content:
                final_content = f"{final_content}\n\nTags: {tag_line}\n"
        path.write_text(final_content, encoding="utf-8")
        return path

    def append_note(self, name: str, additional_content: str) -> None:
        filename = f"{name}.md" if not name.endswith(".md") else name
        path = self.memory_dir / filename
        existing = path.read_text(encoding="utf-8") if path.exists() else f"# {name}\n\n"
        path.write_text(f"{existing}\n\n{additional_content}\n", encoding="utf-8")

    def search(self, query: str) -> List[MemoryRecord]:
        results = []
        query_lower = query.lower()
        for path in self.memory_dir.glob("*.md"):
            record = self.read_note(path.stem)
            if record:
                if query_lower in record.content.lower() or any(query_lower in t.lower() for t in record.tags) or query_lower in record.title.lower():
                    results.append(record)
        return results

    def get_backlinks(self, target_note: str) -> List[str]:
        backlinks = []
        target_clean = target_note.lower()
        for path in self.memory_dir.glob("*.md"):
            record = self.read_note(path.stem)
            if record and path.stem.lower() != target_clean:
                if any(w.lower() == target_clean for w in record.wikilinks):
                    backlinks.append(path.stem)
        return sorted(backlinks)
