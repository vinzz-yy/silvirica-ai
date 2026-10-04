from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from silvirica.core.types import NodeKind

@dataclass
class GraphNode:
    id: str
    kind: NodeKind
    name: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)
