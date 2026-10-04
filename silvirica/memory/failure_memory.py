from __future__ import annotations
import time
from typing import List, Optional
from silvirica.memory.vault import ObsidianMemoryVault

class FailureMemoryManager:
    def __init__(self, vault: ObsidianMemoryVault):
        self.vault = vault

    def record_failure(self, issue: str, attempt: str, result: str, actual_cause: str, verification: str, related_files: Optional[List[str]] = None) -> None:
        date_str = time.strftime("%Y-%m-%d")
        files_str = ", ".join(related_files) if related_files else "None"
        entry = (
            f"### Incident: {issue}\n"
            f"- **Date**: {date_str}\n"
            f"- **Failed Attempt**: {attempt}\n"
            f"- **Result**: {result}\n"
            f"- **Actual Cause**: {actual_cause}\n"
            f"- **Verification / Fix**: {verification}\n"
            f"- **Related Files**: {files_str}\n"
        )
        self.vault.append_note("failures", entry)

    def retrieve_relevant_failures(self, query: str) -> List[str]:
        record = self.vault.read_note("failures")
        if not record:
            return []
        entries = record.content.split("### Incident:")
        matched = []
        q_lower = query.lower()
        for e in entries:
            e = e.strip()
            if not e or e.startswith("#"):
                continue
            if any(term in e.lower() for term in q_lower.split() if len(term) > 3):
                matched.append(f"Incident: {e}")
        return matched
