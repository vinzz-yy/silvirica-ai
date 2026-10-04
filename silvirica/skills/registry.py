from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from silvirica.core.types import SkillLevel

@dataclass
class SkillDefinition:
    name: str
    version: str = "1.0.0"
    description: str = ""
    triggers: List[str] = field(default_factory=list)
    priority: str = "medium"
    summary: str = ""
    instructions: str = ""
    tools: List[str] = field(default_factory=list)
    knowledge: List[str] = field(default_factory=list)

    def render(self, level: SkillLevel) -> str:
        if level == SkillLevel.LEVEL_0_METADATA:
            return f"Skill: {self.name} v{self.version} - {self.description}"
        elif level == SkillLevel.LEVEL_1_SUMMARY:
            tools_str = ", ".join(self.tools) if self.tools else "none"
            return f"### Skill: {self.name} (v{self.version})\nSummary: {self.summary or self.description}\nKey Tools: {tools_str}"
        else:
            knowledge_str = "\n".join(f"- {k}" for k in self.knowledge) if self.knowledge else "Standard"
            tools_str = "\n".join(f"- {t}" for t in self.tools) if self.tools else "Standard"
            return (
                f"## Active Skill: {self.name} (v{self.version})\n{self.description}\n\n"
                f"### Instructions:\n{self.instructions}\n\n"
                f"### Tools Provided:\n{tools_str}\n\n"
                f"### Knowledge Domains:\n{knowledge_str}"
            )
