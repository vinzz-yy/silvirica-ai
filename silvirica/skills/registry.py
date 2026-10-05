from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from silvirica.core.types import SkillLevel


class SkillTrustTier(str, Enum):
    BUILTIN = "BUILTIN"
    VERIFIED = "VERIFIED"
    COMMUNITY = "COMMUNITY"
    LOCAL = "LOCAL"
    UNTRUSTED = "UNTRUSTED"


@dataclass
class SkillCapabilities:
    filesystem: str = "read"  # none, read, write
    network: bool = False
    shell: bool = False
    memory: str = "read"  # none, read, write
    git: str = "read"  # none, read, write

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SkillCapabilities:
        return cls(
            filesystem=str(data.get("filesystem", "read")).lower(),
            network=bool(data.get("network", False)),
            shell=bool(data.get("shell", False)),
            memory=str(data.get("memory", "read")).lower(),
            git=str(data.get("git", "read")).lower(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filesystem": self.filesystem,
            "network": self.network,
            "shell": self.shell,
            "memory": self.memory,
            "git": self.git,
        }


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
    trust_tier: SkillTrustTier = SkillTrustTier.BUILTIN
    capabilities: SkillCapabilities = field(default_factory=SkillCapabilities)
    author: Optional[str] = None
    checksum: Optional[str] = None

    def render(self, level: SkillLevel) -> str:
        if level == SkillLevel.LEVEL_0_METADATA:
            return f"Skill: {self.name} v{self.version} [{self.trust_tier.value}] - {self.description}"
        elif level == SkillLevel.LEVEL_1_SUMMARY:
            tools_str = ", ".join(self.tools) if self.tools else "none"
            return f"### Skill: {self.name} (v{self.version} | {self.trust_tier.value})\nSummary: {self.summary or self.description}\nKey Tools: {tools_str}"
        else:
            knowledge_str = "\n".join(f"- {k}" for k in self.knowledge) if self.knowledge else "Standard"
            tools_str = "\n".join(f"- {t}" for t in self.tools) if self.tools else "Standard"
            caps = self.capabilities.to_dict()
            caps_str = ", ".join(f"{k}: {v}" for k, v in caps.items())
            return (
                f"## Active Skill: {self.name} (v{self.version} | Trust: {self.trust_tier.value})\n"
                f"{self.description}\n\n"
                f"### Capabilities: {caps_str}\n\n"
                f"### Instructions:\n{self.instructions}\n\n"
                f"### Tools Provided:\n{tools_str}\n\n"
                f"### Knowledge Domains:\n{knowledge_str}"
            )
