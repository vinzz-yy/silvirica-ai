from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from silvirica.core.types import RoutingCategory


@dataclass
class CompressedHandoffPacket:
    task: str
    evidence: List[str] = field(default_factory=list)
    relevant_code_snippets: List[str] = field(default_factory=list)
    failed_attempts: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    previous_model: str = ""
    target_category: RoutingCategory = RoutingCategory.CODER

    def to_prompt(self) -> str:
        parts = [
            f"# ESCALATED TASK HANDOFF",
            f"**Task**: {self.task}",
            f"**Previous Tier**: {self.previous_model} -> Escalated to {self.target_category.value}",
        ]
        if self.evidence:
            parts.append("## Evidence Collected:\n" + "\n".join(f"- {e}" for e in self.evidence))
        if self.relevant_code_snippets:
            parts.append("## Relevant Code Context:\n" + "\n".join(self.relevant_code_snippets))
        if self.failed_attempts:
            parts.append("## Failed Hypotheses / Attempts:\n" + "\n".join(f"- {f}" for f in self.failed_attempts))
        if self.constraints:
            parts.append("## Project Constraints:\n" + "\n".join(f"- {c}" for c in self.constraints))
        if self.open_questions:
            parts.append("## Open Questions:\n" + "\n".join(f"- {q}" for q in self.open_questions))
        return "\n\n".join(parts)


class EscalationManager:
    """
    Manages automatic model escalation using compressed handoff packets.
    Prevents re-sending bloated conversation histories during escalation.
    """

    @classmethod
    def create_handoff(
        cls,
        task: str,
        evidence: Optional[List[str]] = None,
        code_snippets: Optional[List[str]] = None,
        failed_attempts: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
        current_category: RoutingCategory = RoutingCategory.QUICK,
    ) -> CompressedHandoffPacket:
        # Determine next escalation category
        next_cat = RoutingCategory.CODER
        if current_category == RoutingCategory.QUICK:
            next_cat = RoutingCategory.CODER
        elif current_category == RoutingCategory.CODER:
            next_cat = RoutingCategory.DEEP
        elif current_category == RoutingCategory.DEEP:
            next_cat = RoutingCategory.ULTRABRAIN

        return CompressedHandoffPacket(
            task=task,
            evidence=evidence or [],
            relevant_code_snippets=code_snippets or [],
            failed_attempts=failed_attempts or [],
            constraints=constraints or [],
            open_questions=open_questions or [],
            previous_model=current_category.value,
            target_category=next_cat,
        )
