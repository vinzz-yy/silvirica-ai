from __future__ import annotations
import time
from typing import List, Optional
from silvirica.memory.vault import ObsidianMemoryVault

class DecisionMemoryManager:
    def __init__(self, vault: ObsidianMemoryVault):
        self.vault = vault

    def record_decision(self, title: str, status: str = "Accepted", context: str = "", decision: str = "", consequences: str = "", tags: Optional[List[str]] = None) -> None:
        date_str = time.strftime("%Y-%m-%d")
        entry = (
            f"### ADR: {title}\n"
            f"- **Date**: {date_str}\n"
            f"- **Status**: {status}\n"
            f"- **Context**: {context}\n"
            f"- **Decision**: {decision}\n"
            f"- **Consequences**: {consequences}\n"
        )
        self.vault.append_note("decisions", entry)

    def get_decisions(self) -> str:
        record = self.vault.read_note("decisions")
        return record.content if record else "No architecture decisions recorded yet."
