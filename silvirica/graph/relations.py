from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict
from silvirica.core.types import RelationKind

@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    relation: RelationKind
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
